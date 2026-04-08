"""Stripe + Toss Payments 결제 연동 API 라우터."""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import uuid
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from yaa_core.database.engine import get_db_session
from yaa_core.database.repositories import (
    SubscriptionRepository,
    WorkspaceRepository,
)
from yaa_core.shared.config import PLAN_QUOTAS, AppSettings

from yaa_app.api.auth import AuthContext, get_auth_context
from yaa_app.api.dependencies import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# Pydantic 스키마
# ============================================


class CheckoutRequest(BaseModel):
    """결제 체크아웃 요청."""

    plan: str  # "pro" or "enterprise"


class CheckoutResponse(BaseModel):
    """결제 체크아웃 응답."""

    checkout_url: str


class PortalResponse(BaseModel):
    """고객 포털 응답."""

    portal_url: str


class SubscriptionResponse(BaseModel):
    """구독 상태 응답."""

    plan: str
    status: str
    current_period_end: str | None = None


# ============================================
# 헬퍼 함수
# ============================================


def _get_stripe():
    """stripe 모듈을 lazy import 합니다."""
    try:
        import stripe

        return stripe
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Stripe 모듈이 설치되지 않았습니다. billing extras를 설치하세요.",
        ) from exc


def _get_price_id(plan: str, settings: AppSettings) -> str:
    """요금제에 해당하는 Stripe Price ID를 반환합니다."""
    price_map = {
        "pro": settings.stripe_price_pro,
        "enterprise": settings.stripe_price_enterprise,
    }
    price_id = price_map.get(plan, "")
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"유효하지 않은 요금제입니다: {plan}",
        )
    return price_id


def _require_stripe_config(settings: AppSettings) -> None:
    """Stripe 설정이 유효한지 확인합니다."""
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Stripe가 구성되지 않았습니다.",
        )


# ============================================
# 엔드포인트
# ============================================


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    body: CheckoutRequest,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    settings: AppSettings = Depends(get_settings),
) -> CheckoutResponse:
    """Stripe Checkout 세션을 생성합니다."""
    _require_stripe_config(settings)
    stripe = _get_stripe()
    stripe.api_key = settings.stripe_secret_key

    if body.plan not in ("pro", "enterprise"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 요금제입니다. 'pro' 또는 'enterprise'만 가능합니다.",
        )

    workspace_id = auth.workspace_id
    if not workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="워크스페이스가 필요합니다.",
        )

    price_id = _get_price_id(body.plan, settings)

    # 기존 구독 확인
    sub_repo = SubscriptionRepository(session)
    existing = await sub_repo.get_by_workspace(workspace_id)
    customer_id = existing.stripe_customer_id if existing else None

    # Stripe 고객이 없으면 새로 생성
    if not customer_id:
        customer = stripe.Customer.create(
            metadata={"workspace_id": workspace_id},
        )
        customer_id = customer.id

    # Checkout 세션 생성
    cors_origin = settings.cors_origins.split(",")[0].strip()
    checkout_session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{cors_origin}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{cors_origin}/billing/cancel",
        metadata={"workspace_id": workspace_id, "plan": body.plan},
    )

    logger.info("Checkout 세션 생성: workspace=%s plan=%s", workspace_id, body.plan)
    return CheckoutResponse(checkout_url=checkout_session.url)


@router.post("/portal", response_model=PortalResponse)
async def create_portal_session(
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    settings: AppSettings = Depends(get_settings),
) -> PortalResponse:
    """Stripe Customer Portal 세션을 생성합니다."""
    _require_stripe_config(settings)
    stripe = _get_stripe()
    stripe.api_key = settings.stripe_secret_key

    workspace_id = auth.workspace_id
    if not workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="워크스페이스가 필요합니다.",
        )

    sub_repo = SubscriptionRepository(session)
    subscription = await sub_repo.get_by_workspace(workspace_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="구독 정보를 찾을 수 없습니다.",
        )

    cors_origin = settings.cors_origins.split(",")[0].strip()
    portal_session = stripe.billing_portal.Session.create(
        customer=subscription.stripe_customer_id,
        return_url=f"{cors_origin}/settings",
    )

    return PortalResponse(portal_url=portal_session.url)


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> SubscriptionResponse:
    """현재 워크스페이스의 구독 상태를 반환합니다."""
    workspace_id = auth.workspace_id
    if not workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="워크스페이스가 필요합니다.",
        )

    sub_repo = SubscriptionRepository(session)
    subscription = await sub_repo.get_by_workspace(workspace_id)

    if not subscription:
        return SubscriptionResponse(plan="free", status="active")

    return SubscriptionResponse(
        plan=subscription.plan,
        status=subscription.status,
        current_period_end=(
            subscription.current_period_end.isoformat() if subscription.current_period_end else None
        ),
    )


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    settings: AppSettings = Depends(get_settings),
) -> dict:
    """Stripe 웹훅을 처리합니다.

    인증 불필요 - Stripe 서명 검증으로 대체.
    """
    _require_stripe_config(settings)
    stripe = _get_stripe()
    stripe.api_key = settings.stripe_secret_key

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not settings.stripe_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="웹훅 시크릿이 구성되지 않았습니다.",
        )

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="잘못된 페이로드입니다.",
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="서명 검증에 실패했습니다.",
        )

    event_type = event["type"]
    data = event["data"]["object"]

    logger.info("Stripe 웹훅 수신: type=%s", event_type)

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(data, session)
    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(data, session, settings)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(data, session)

    await session.commit()
    return {"status": "ok"}


# ============================================
# 웹훅 핸들러
# ============================================


async def _handle_checkout_completed(data: dict, session: AsyncSession) -> None:
    """checkout.session.completed 이벤트를 처리합니다."""
    workspace_id = data.get("metadata", {}).get("workspace_id")
    plan = data.get("metadata", {}).get("plan", "pro")
    customer_id = data.get("customer")
    subscription_id = data.get("subscription")

    if not workspace_id or not customer_id:
        logger.warning("Checkout 완료 이벤트에 workspace_id 또는 customer_id 누락")
        return

    sub_repo = SubscriptionRepository(session)
    ws_repo = WorkspaceRepository(session)

    existing = await sub_repo.get_by_workspace(workspace_id)
    if existing:
        await sub_repo.update(
            existing.id,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            plan=plan,
            status="active",
        )
    else:
        await sub_repo.create(
            subscription_id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            plan=plan,
            status="active",
        )

    # 워크스페이스 플랜 & 쿼터 업데이트
    quotas = PLAN_QUOTAS.get(plan, PLAN_QUOTAS["free"])
    await ws_repo.update(
        workspace_id,
        plan=plan,
        pipeline_quota=quotas["monthly_pipelines"],
        channel_quota=quotas["max_channels"],
    )

    logger.info("구독 생성/업데이트: workspace=%s plan=%s", workspace_id, plan)


async def _handle_subscription_updated(
    data: dict, session: AsyncSession, settings: AppSettings | None = None
) -> None:
    """customer.subscription.updated 이벤트를 처리합니다."""
    stripe_sub_id = data.get("id")
    if not stripe_sub_id:
        return

    sub_repo = SubscriptionRepository(session)
    subscription = await sub_repo.get_by_stripe_subscription(stripe_sub_id)
    if not subscription:
        logger.warning("구독을 찾을 수 없음: stripe_subscription_id=%s", stripe_sub_id)
        return

    new_status = data.get("status", "active")
    # Stripe 구독 상태를 매핑
    status_map = {
        "active": "active",
        "past_due": "past_due",
        "canceled": "canceled",
        "unpaid": "past_due",
        "incomplete": "past_due",
        "trialing": "active",
    }
    mapped_status = status_map.get(new_status, "active")

    # 기간 정보 업데이트
    period_start = data.get("current_period_start")
    period_end = data.get("current_period_end")

    update_kwargs: dict = {"status": mapped_status}
    if period_start:
        update_kwargs["current_period_start"] = datetime.fromtimestamp(period_start, tz=UTC)
    if period_end:
        update_kwargs["current_period_end"] = datetime.fromtimestamp(period_end, tz=UTC)

    # 요금제 변경 확인 (items.data[0].price)
    items = data.get("items", {}).get("data", [])
    if items:
        price_id = items[0].get("price", {}).get("id", "")
        if price_id:
            update_kwargs["plan"] = _price_id_to_plan(price_id, settings)

    await sub_repo.update(subscription.id, **update_kwargs)

    # 워크스페이스 플랜도 동기화
    if "plan" in update_kwargs:
        ws_repo = WorkspaceRepository(session)
        plan = update_kwargs["plan"]
        quotas = PLAN_QUOTAS.get(plan, PLAN_QUOTAS["free"])
        await ws_repo.update(
            subscription.workspace_id,
            plan=plan,
            pipeline_quota=quotas["monthly_pipelines"],
            channel_quota=quotas["max_channels"],
        )

    logger.info(
        "구독 업데이트: subscription=%s status=%s",
        subscription.id,
        mapped_status,
    )


async def _handle_subscription_deleted(data: dict, session: AsyncSession) -> None:
    """customer.subscription.deleted 이벤트를 처리합니다."""
    stripe_sub_id = data.get("id")
    if not stripe_sub_id:
        return

    sub_repo = SubscriptionRepository(session)
    subscription = await sub_repo.get_by_stripe_subscription(stripe_sub_id)
    if not subscription:
        logger.warning("구독을 찾을 수 없음: stripe_subscription_id=%s", stripe_sub_id)
        return

    await sub_repo.update(subscription.id, status="canceled", plan="free")

    # 워크스페이스를 free 플랜으로 다운그레이드
    ws_repo = WorkspaceRepository(session)
    quotas = PLAN_QUOTAS["free"]
    await ws_repo.update(
        subscription.workspace_id,
        plan="free",
        pipeline_quota=quotas["monthly_pipelines"],
        channel_quota=quotas["max_channels"],
    )

    logger.info("구독 해지: workspace=%s", subscription.workspace_id)


def _price_id_to_plan(price_id: str, settings: AppSettings | None = None) -> str:
    """Stripe Price ID를 요금제 이름으로 변환합니다."""
    if settings:
        price_map = {
            settings.stripe_price_pro: "pro",
            settings.stripe_price_enterprise: "enterprise",
        }
        plan = price_map.get(price_id)
        if plan:
            return plan

    # settings 매핑 실패 시 Price ID 접미사로 추론 (폴백)
    if "enterprise" in price_id.lower():
        return "enterprise"
    return "pro"


# ============================================
# Toss Payments 엔드포인트
# ============================================

_TOSS_API_BASE = "https://api.tosspayments.com/v1"
_TOSS_ORDER_PREFIX = "yaa"


def _get_toss_auth_header(secret_key: str) -> str:
    """Toss Payments Basic Auth 헤더를 생성합니다."""
    credentials = base64.b64encode(f"{secret_key}:".encode()).decode()
    return f"Basic {credentials}"


def _require_toss_config(settings: AppSettings) -> None:
    """Toss Payments 설정이 유효한지 확인합니다."""
    if not settings.toss_secret_key:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Toss Payments가 구성되지 않았습니다.",
        )


def _require_toss_checkout_config(settings: AppSettings) -> None:
    """Toss 결제창 호출에 필요한 설정이 유효한지 확인합니다."""
    _require_toss_config(settings)
    if not settings.toss_client_key:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Toss Payments client key가 구성되지 않았습니다.",
        )


def _build_toss_order_id(workspace_id: str, plan: str) -> str:
    """Toss 주문 ID를 생성합니다."""
    return f"{_TOSS_ORDER_PREFIX}-{plan}-{workspace_id[:8]}-{uuid.uuid4().hex[:8]}"


def _extract_toss_plan(order_id: str) -> str:
    """Toss 주문 ID에서 요금제 이름을 추출합니다."""
    parts = order_id.split("-")
    if len(parts) < 4 or parts[0] != _TOSS_ORDER_PREFIX:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 주문 ID입니다.",
        )

    plan = parts[1]
    if plan not in _TOSS_PLAN_AMOUNTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 요금제 주문입니다.",
        )
    return plan


def _verify_toss_order_ownership(order_id: str, workspace_id: str) -> None:
    """Toss 주문 ID가 현재 인증된 워크스페이스에서 발급된 것인지 검증합니다.

    주문 ID 형식: yaa-{plan}-{workspace_id[:8]}-{random}
    """
    parts = order_id.split("-")
    # 최소 4개 파트: prefix, plan, ws_prefix, random
    if len(parts) < 4 or parts[0] != _TOSS_ORDER_PREFIX:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 주문 ID입니다.",
        )
    embedded_ws_prefix = parts[2]
    if not workspace_id.startswith(embedded_ws_prefix):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="주문 ID가 현재 워크스페이스에서 발급된 것이 아닙니다.",
        )


class TossCheckoutRequest(BaseModel):
    """Toss 결제 요청."""

    plan: str  # "pro" or "enterprise"
    order_name: str = "YAA Pro 구독"


class TossCheckoutResponse(BaseModel):
    """Toss 결제 응답 (프론트엔드로 결제창 파라미터 전달)."""

    client_key: str
    customer_key: str
    amount: int
    order_id: str
    order_name: str
    customer_name: str | None = None


class TossConfirmRequest(BaseModel):
    """Toss 결제 승인 요청."""

    payment_key: str
    order_id: str
    amount: int


class TossConfirmResponse(BaseModel):
    """Toss 결제 승인 응답."""

    payment_key: str
    order_id: str
    status: str
    plan: str


_TOSS_PLAN_AMOUNTS = {
    "pro": 29000,
    "enterprise": 99000,
}

_TOSS_PLAN_ORDER_NAMES = {
    "pro": "YAA Pro 구독",
    "enterprise": "YAA Enterprise 구독",
}


@router.post("/toss/checkout", response_model=TossCheckoutResponse)
async def create_toss_checkout(
    body: TossCheckoutRequest,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    settings: AppSettings = Depends(get_settings),
) -> TossCheckoutResponse:
    """Toss Payments 결제창 파라미터를 생성합니다."""
    _require_toss_checkout_config(settings)

    if body.plan not in ("pro", "enterprise"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 요금제입니다. 'pro' 또는 'enterprise'만 가능합니다.",
        )

    workspace_id = auth.workspace_id
    if not workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="워크스페이스가 필요합니다.",
        )

    amount = _TOSS_PLAN_AMOUNTS[body.plan]
    order_id = _build_toss_order_id(workspace_id, body.plan)
    order_name = (
        body.order_name
        if body.order_name != TossCheckoutRequest.model_fields["order_name"].default
        else _TOSS_PLAN_ORDER_NAMES[body.plan]
    )

    logger.info(
        "Toss Checkout 파라미터 생성: workspace=%s plan=%s",
        workspace_id,
        body.plan,
    )

    return TossCheckoutResponse(
        client_key=settings.toss_client_key,
        customer_key=workspace_id,
        amount=amount,
        order_id=order_id,
        order_name=order_name,
    )


@router.post("/toss/confirm", response_model=TossConfirmResponse)
async def confirm_toss_payment(
    body: TossConfirmRequest,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    settings: AppSettings = Depends(get_settings),
) -> TossConfirmResponse:
    """Toss Payments 결제를 승인하고 플랜을 업데이트합니다."""
    _require_toss_config(settings)

    workspace_id = auth.workspace_id
    if not workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="워크스페이스가 필요합니다.",
        )

    plan = _extract_toss_plan(body.order_id)

    # 소유권 검증: 주문 ID의 워크스페이스 prefix가 현재 인증 사용자와 일치하는지 확인
    _verify_toss_order_ownership(body.order_id, workspace_id)

    expected_amount = _TOSS_PLAN_AMOUNTS[plan]
    if body.amount != expected_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="결제 금액이 선택한 요금제와 일치하지 않습니다.",
        )

    # 멱등성 처리: 이미 승인된 payment_key인지 확인
    sub_repo_check = SubscriptionRepository(session)
    existing_payment = await sub_repo_check.get_by_stripe_customer(body.payment_key)
    if existing_payment and existing_payment.status == "active":
        logger.info(
            "Toss 결제 중복 요청 (이미 처리됨): payment_key=%s workspace=%s",
            body.payment_key,
            workspace_id,
        )
        return TossConfirmResponse(
            payment_key=body.payment_key,
            order_id=body.order_id,
            status="DONE",
            plan=existing_payment.plan,
        )

    # Toss Payments 결제 승인 API 호출
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_TOSS_API_BASE}/payments/confirm",
            headers={
                "Authorization": _get_toss_auth_header(settings.toss_secret_key),
                "Content-Type": "application/json",
            },
            json={
                "paymentKey": body.payment_key,
                "orderId": body.order_id,
                "amount": body.amount,
            },
        )

    if response.status_code != 200:
        try:
            error_data = response.json()
            error_message = error_data.get("message", "알 수 없는 오류")
        except ValueError:
            error_data = {"raw": response.text}
            error_message = response.text or "알 수 없는 오류"

        logger.error("Toss 결제 승인 실패: %s", error_data)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"결제 승인에 실패했습니다: {error_message}",
        )

    payment_data = response.json()
    toss_status = payment_data.get("status", "")

    if toss_status == "DONE":
        # 구독 생성/업데이트
        sub_repo = SubscriptionRepository(session)
        ws_repo = WorkspaceRepository(session)

        existing = await sub_repo.get_by_workspace(workspace_id)
        toss_payment_key = payment_data.get("paymentKey", body.payment_key)

        if existing:
            await sub_repo.update(
                existing.id,
                plan=plan,
                status="active",
                stripe_subscription_id=toss_payment_key,
            )
        else:
            await sub_repo.create(
                subscription_id=str(uuid.uuid4()),
                workspace_id=workspace_id,
                stripe_customer_id=workspace_id,
                stripe_subscription_id=toss_payment_key,
                plan=plan,
                status="active",
            )

        quotas = PLAN_QUOTAS.get(plan, PLAN_QUOTAS["free"])
        await ws_repo.update(
            workspace_id,
            plan=plan,
            pipeline_quota=quotas["monthly_pipelines"],
            channel_quota=quotas["max_channels"],
        )
        await session.commit()

        logger.info("Toss 결제 승인 완료: workspace=%s plan=%s", workspace_id, plan)

    return TossConfirmResponse(
        payment_key=body.payment_key,
        order_id=body.order_id,
        status=toss_status,
        plan=plan,
    )


@router.post("/toss/webhook", include_in_schema=False)
async def toss_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    settings: AppSettings = Depends(get_settings),
) -> dict:
    """Toss Payments 웹훅을 처리합니다.

    정기결제(빌링) 이벤트 처리.
    """
    _require_toss_config(settings)

    payload = await request.body()

    # Toss Payments 웹훅 서명 검증 (필수)
    if not settings.toss_webhook_secret:
        logger.error("TOSS_WEBHOOK_SECRET이 설정되지 않아 웹훅을 거부합니다.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="웹훅 시크릿이 설정되지 않았습니다.",
        )

    sig_header = request.headers.get("X-Toss-Signature", "")
    expected_sig = hmac.new(
        settings.toss_webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(sig_header, expected_sig):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="웹훅 서명 검증에 실패했습니다.",
        )

    import json

    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="잘못된 페이로드입니다.",
        )

    event_type = event.get("eventType", "")
    logger.info("Toss 웹훅 수신: type=%s", event_type)

    # 정기결제 상태 변경
    if event_type == "PAYMENT_STATUS_CHANGED":
        data = event.get("data", {})
        toss_status = data.get("status", "")
        order_id = data.get("orderId", "")
        payment_key = data.get("paymentKey", "")

        logger.info(
            "Toss 결제 상태 변경: order_id=%s status=%s payment_key=%s",
            order_id,
            toss_status,
            payment_key,
        )

        if toss_status == "DONE" and payment_key:
            sub_repo = SubscriptionRepository(session)
            subscription = await sub_repo.get_by_stripe_subscription(payment_key)
            if subscription:
                await sub_repo.update(subscription.id, status="active")

        elif toss_status in ("CANCELED", "PARTIAL_CANCELED"):
            sub_repo = SubscriptionRepository(session)
            subscription = await sub_repo.get_by_stripe_subscription(payment_key)
            if subscription:
                await sub_repo.update(subscription.id, status="canceled")
            logger.info("Toss 결제 취소: order_id=%s", order_id)

    await session.commit()
    return {"status": "ok"}

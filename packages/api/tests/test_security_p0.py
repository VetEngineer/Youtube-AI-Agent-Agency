"""P0 보안/결제 수정 회귀 테스트 (#73).

#68 인증/보안, #69 결제 보안 수정사항 검증.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from yaa_app.api.routes.billing import (
    _build_toss_order_id,
    _extract_toss_plan,
    _price_id_to_plan,
    _verify_toss_order_ownership,
)
from yaa_core.shared.config import ChannelRegistry
from yaa_core.shared.encryption import decrypt_value, encrypt_value

# ============================================
# #68 인증/보안 테스트
# ============================================


class TestChannelRegistryPathTraversal:
    """ChannelRegistry workspace_id 경로 순회 방지 테스트."""

    def test_정상_workspace_id_허용(self, tmp_path):
        registry = ChannelRegistry(channels_dir=str(tmp_path))
        scoped = registry.for_workspace("abc-123_test")
        assert "abc-123_test" in str(scoped.channels_dir)

    @pytest.mark.parametrize(
        "bad_id",
        [
            "../../../etc",
            "../../passwd",
            "foo/bar",
            "foo bar",
            "",
            "hello world",
            "a;rm -rf /",
        ],
    )
    def test_경로순회_workspace_id_거부(self, tmp_path, bad_id):
        registry = ChannelRegistry(channels_dir=str(tmp_path))
        with pytest.raises(ValueError, match="유효하지 않은 workspace_id"):
            registry.for_workspace(bad_id)

    def test_생성자에서도_경로순회_방지(self, tmp_path):
        with pytest.raises(ValueError, match="유효하지 않은 workspace_id"):
            ChannelRegistry(channels_dir=str(tmp_path), workspace_id="../escape")


class TestEncryption:
    """암호화 라운드트립 + 키 부재 테스트."""

    def test_키_미설정시_RuntimeError(self, monkeypatch):
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
        with pytest.raises(RuntimeError, match="ENCRYPTION_KEY"):
            encrypt_value("test_secret")

    def test_암호화_복호화_라운드트립(self, monkeypatch):
        from cryptography.fernet import Fernet

        key = Fernet.generate_key().decode()
        monkeypatch.setenv("ENCRYPTION_KEY", key)

        plaintext = "yaa_super_secret_api_key_12345"
        encrypted = encrypt_value(plaintext)
        assert encrypted.startswith("enc:")
        assert encrypted != plaintext

        decrypted = decrypt_value(encrypted)
        assert decrypted == plaintext

    def test_비암호화_값은_원문_반환(self):
        assert decrypt_value("plain_text") == "plain_text"


class TestJwtSecretMinLength:
    """JWT 시크릿 최소 길이 검증 테스트."""

    def test_짧은_jwt_시크릿_거부(self):
        from yaa_app.api.auth import _decode_jwt
        from yaa_core.shared.config import AppSettings

        settings = AppSettings(jwt_secret="short")  # 5자 < 32자 최소
        result = _decode_jwt("fake.jwt.token", settings)
        assert result is None

    def test_빈_jwt_시크릿_거부(self):
        from yaa_app.api.auth import _decode_jwt
        from yaa_core.shared.config import AppSettings

        settings = AppSettings(jwt_secret="")
        result = _decode_jwt("fake.jwt.token", settings)
        assert result is None


# ============================================
# #69 결제 보안 테스트
# ============================================


class TestTossOrderOwnership:
    """Toss 주문 소유권 검증 테스트."""

    def test_정상_소유권_통과(self):
        workspace_id = "12345678-abcd-efgh-ijkl-1234567890ab"
        order_id = _build_toss_order_id(workspace_id, "pro")
        _verify_toss_order_ownership(order_id, workspace_id)  # 예외 없음

    def test_다른_워크스페이스_403(self):
        workspace_id = "12345678-abcd-efgh-ijkl-1234567890ab"
        other_ws = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        order_id = _build_toss_order_id(workspace_id, "pro")

        with pytest.raises(HTTPException) as exc_info:
            _verify_toss_order_ownership(order_id, other_ws)
        assert exc_info.value.status_code == 403


class TestTossIdempotency:
    """Toss confirm 멱등성 관련 테스트 (유틸 함수 레벨)."""

    def test_동일_order_id에서_동일_plan_추출(self):
        workspace_id = "12345678-abcd-efgh-ijkl-1234567890ab"
        order_id = _build_toss_order_id(workspace_id, "enterprise")
        assert _extract_toss_plan(order_id) == "enterprise"

    @pytest.mark.parametrize("bad_order", ["invalid", "yaa", "random-string"])
    def test_유효하지않은_order_id_400(self, bad_order):
        with pytest.raises(HTTPException) as exc_info:
            _extract_toss_plan(bad_order)
        assert exc_info.value.status_code == 400


class TestPriceIdToPlan:
    """_price_id_to_plan 문자열 폴백 제거 테스트."""

    def test_설정_없으면_free_폴백(self):
        result = _price_id_to_plan("price_unknown_123")
        assert result == "free"

    def test_enterprise_문자열매칭_안됨(self):
        # 이전에는 "enterprise"가 포함되면 enterprise를 반환했으나,
        # 이제는 free로 안전 폴백
        result = _price_id_to_plan("price_enterprise_test", settings=None)
        assert result == "free"

    def test_설정_매핑_성공(self):
        from yaa_core.shared.config import AppSettings

        settings = AppSettings(
            stripe_price_pro="price_pro_123",
            stripe_price_enterprise="price_ent_456",
        )
        assert _price_id_to_plan("price_pro_123", settings) == "pro"
        assert _price_id_to_plan("price_ent_456", settings) == "enterprise"

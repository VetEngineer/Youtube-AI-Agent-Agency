"""결제 유틸리티 테스트."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from yaa_app.api.routes.billing import _build_toss_order_id, _extract_toss_plan


def test_toss_order_id에_플랜과_workspace_prefix가_포함된다():
    workspace_id = "12345678-abcd-efgh-ijkl-1234567890ab"

    order_id = _build_toss_order_id(workspace_id, "pro")

    ws_compact = workspace_id.replace("-", "")
    assert order_id.startswith(f"yaa-pro-{ws_compact}-")
    assert _extract_toss_plan(order_id) == "pro"


def test_toss_order_id에서_enterprise_플랜을_추출한다():
    workspace_id = "abcdef12-3456-7890-abcd-ef1234567890"

    order_id = _build_toss_order_id(workspace_id, "enterprise")

    assert _extract_toss_plan(order_id) == "enterprise"


@pytest.mark.parametrize("order_id", ["invalid", "yaa-unknown-12345678-deadbeef"])
def test_유효하지_않은_toss_order_id는_400을_반환한다(order_id: str):
    with pytest.raises(HTTPException) as exc_info:
        _extract_toss_plan(order_id)

    assert exc_info.value.status_code == 400

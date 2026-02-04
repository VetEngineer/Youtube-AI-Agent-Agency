"""API 인증 모듈 테스트."""

from __future__ import annotations

import pytest

from src.api.auth import (
    API_KEY_PREFIX,
    generate_api_key,
    generate_key_id,
    hash_api_key,
)
from src.database.engine import init_db, set_session_factory
from src.database.repositories import ApiKeyRepository

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture()
async def session_factory():
    """테스트용 인메모리 DB 세션 팩토리."""
    factory = await init_db(TEST_DB_URL)
    yield factory
    set_session_factory(None)


@pytest.fixture()
async def session(session_factory):
    """테스트용 DB 세션."""
    async with session_factory() as s:
        yield s


# ============================================
# 키 생성 / 해싱 테스트
# ============================================


class TestKeyGeneration:
    """API 키 생성 관련 테스트."""

    def test_generate_api_key_접두사(self):
        key = generate_api_key()
        assert key.startswith(API_KEY_PREFIX)

    def test_generate_api_key_길이(self):
        key = generate_api_key()
        assert len(key) > len(API_KEY_PREFIX) + 20

    def test_generate_api_key_고유성(self):
        keys = {generate_api_key() for _ in range(100)}
        assert len(keys) == 100

    def test_hash_api_key_결정적(self):
        key = "yaa_test123"
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)
        assert hash1 == hash2

    def test_hash_api_key_다른_입력_다른_해시(self):
        hash1 = hash_api_key("yaa_key1")
        hash2 = hash_api_key("yaa_key2")
        assert hash1 != hash2

    def test_generate_key_id_uuid_형식(self):
        key_id = generate_key_id()
        parts = key_id.split("-")
        assert len(parts) == 5


# ============================================
# DB 연동 인증 테스트
# ============================================


class TestAuthWithDB:
    """DB 기반 인증 테스트."""

    async def test_키_생성_및_해시_검증(self, session):
        plaintext_key = generate_api_key()
        key_hash = hash_api_key(plaintext_key)
        key_id = generate_key_id()

        repo = ApiKeyRepository(session)
        await repo.create(
            key_id=key_id,
            key_hash=key_hash,
            name="테스트 키",
            scopes=["read", "write"],
        )
        await session.flush()

        # 올바른 키로 조회
        found = await repo.get_by_hash(key_hash)
        assert found is not None
        assert found.id == key_id

        # 잘못된 키로 조회
        wrong_hash = hash_api_key("yaa_wrong_key")
        not_found = await repo.get_by_hash(wrong_hash)
        assert not_found is None

    async def test_비활성_키는_조회_불가(self, session):
        plaintext_key = generate_api_key()
        key_hash = hash_api_key(plaintext_key)
        key_id = generate_key_id()

        repo = ApiKeyRepository(session)
        await repo.create(key_id=key_id, key_hash=key_hash, name="삭제될 키")
        await repo.deactivate(key_id)
        await session.flush()

        found = await repo.get_by_hash(key_hash)
        assert found is None

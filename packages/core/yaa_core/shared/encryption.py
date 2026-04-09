"""API 키 등 민감 데이터의 대칭 암호화 유틸리티."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_ENCRYPTION_KEY_ENV = "ENCRYPTION_KEY"


def _get_fernet_key() -> bytes | None:
    """환경변수에서 Fernet 암호화 키를 가져옵니다."""
    key = os.environ.get(_ENCRYPTION_KEY_ENV, "")
    if not key:
        return None
    return key.encode()


def generate_encryption_key() -> str:
    """새 Fernet 암호화 키를 생성합니다 (설정용)."""
    from cryptography.fernet import Fernet

    return Fernet.generate_key().decode()


def encrypt_value(plaintext: str) -> str:
    """평문을 암호화합니다. 키가 없으면 RuntimeError 발생."""
    key = _get_fernet_key()
    if not key:
        raise RuntimeError(
            "ENCRYPTION_KEY가 설정되지 않았습니다. "
            "API 키 암호화를 위해 ENCRYPTION_KEY 환경변수를 설정하세요."
        )
    from cryptography.fernet import Fernet

    f = Fernet(key)
    return "enc:" + f.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """암호문을 복호화합니다. enc: 접두사가 없으면 원문(레거시) 반환."""
    if not ciphertext.startswith("enc:"):
        return ciphertext

    key = _get_fernet_key()
    if not key:
        logger.warning("ENCRYPTION_KEY 미설정, 복호화 불가")
        return ""
    try:
        from cryptography.fernet import Fernet

        f = Fernet(key)
        return f.decrypt(ciphertext[4:].encode()).decode()
    except Exception:
        logger.error("복호화 실패")
        return ""


def is_encrypted(value: str) -> bool:
    """값이 암호화되었는지 확인합니다."""
    return value.startswith("enc:")

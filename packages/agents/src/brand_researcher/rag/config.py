"""RAG 설정."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


class RAGConfig(BaseSettings):
    """RAG 벡터 스토리지 설정."""

    rag_enabled: bool = False
    rag_persist_dir: str = "./data/chroma"
    rag_collection_prefix: str = "yaa_brand"
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50
    rag_top_k: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "env_prefix": ""}

    @property
    def persist_path(self) -> Path:
        return Path(self.rag_persist_dir)

    def collection_name(self, channel_id: str) -> str:
        """채널별 ChromaDB 컬렉션 이름을 반환합니다."""
        return f"{self.rag_collection_prefix}_{channel_id}"

"""브랜드 자료를 ChromaDB에 인덱싱하는 모듈."""

from __future__ import annotations

import logging
from pathlib import Path

from .config import RAGConfig

logger = logging.getLogger(__name__)


class BrandIndexer:
    """brand_guide.yaml과 수집 자료를 벡터 스토리지에 인덱싱합니다."""

    def __init__(self, config: RAGConfig | None = None) -> None:
        self._config = config or RAGConfig()
        self._client = None

    def _get_client(self):
        """ChromaDB 클라이언트를 lazy 초기화합니다."""
        if self._client is not None:
            return self._client

        import chromadb

        self._config.persist_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(self._config.persist_path),
        )
        return self._client

    def _chunk_text(self, text: str) -> list[str]:
        """텍스트를 설정된 크기의 청크로 분할합니다."""
        if not text.strip():
            return []

        chunks = []
        size = self._config.rag_chunk_size
        overlap = self._config.rag_chunk_overlap

        start = 0
        while start < len(text):
            end = start + size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start += size - overlap

        return chunks

    def index_brand_guide(self, channel_id: str, guide_path: Path) -> int:
        """brand_guide.yaml을 인덱싱합니다.

        Returns:
            인덱싱된 청크 수
        """
        if not guide_path.exists():
            logger.warning("brand_guide.yaml을 찾을 수 없습니다: %s", guide_path)
            return 0

        content = guide_path.read_text(encoding="utf-8")
        return self._index_documents(
            channel_id=channel_id,
            documents=[content],
            source_type="brand_guide",
            source_names=["brand_guide.yaml"],
        )

    def index_sources(self, channel_id: str, sources_dir: Path) -> int:
        """sources/ 디렉토리의 문서를 인덱싱합니다.

        Returns:
            인덱싱된 청크 수
        """
        if not sources_dir.exists():
            return 0

        documents = []
        names = []
        for file_path in sorted(sources_dir.iterdir()):
            if file_path.suffix in (".txt", ".md", ".yaml"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    documents.append(content)
                    names.append(file_path.name)
                except Exception:
                    logger.warning("파일 읽기 실패: %s", file_path)
                    continue

        if not documents:
            return 0

        return self._index_documents(
            channel_id=channel_id,
            documents=documents,
            source_type="source_document",
            source_names=names,
        )

    def index_collection_results(
        self,
        channel_id: str,
        sources: list[dict[str, str]],
    ) -> int:
        """수집 결과(CollectedSource 딕셔너리 리스트)를 인덱싱합니다.

        Args:
            channel_id: 채널 ID
            sources: [{"title": ..., "content": ..., "source_type": ...}, ...]

        Returns:
            인덱싱된 청크 수
        """
        documents = [s.get("content", "") for s in sources if s.get("content")]
        names = [s.get("title", "unknown") for s in sources if s.get("content")]
        source_type = "collected"

        if not documents:
            return 0

        return self._index_documents(
            channel_id=channel_id,
            documents=documents,
            source_type=source_type,
            source_names=names,
        )

    def _index_documents(
        self,
        channel_id: str,
        documents: list[str],
        source_type: str,
        source_names: list[str],
    ) -> int:
        """문서를 청크로 분할하여 ChromaDB에 저장합니다."""
        client = self._get_client()
        collection_name = self._config.collection_name(channel_id)
        collection = client.get_or_create_collection(name=collection_name)

        all_chunks = []
        all_metadatas = []
        all_ids = []

        for doc, name in zip(documents, source_names):
            chunks = self._chunk_text(doc)
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_metadatas.append({
                    "source_type": source_type,
                    "source_name": name,
                    "chunk_index": i,
                })
                all_ids.append(f"{channel_id}_{source_type}_{name}_{i}")

        if not all_chunks:
            return 0

        collection.upsert(
            documents=all_chunks,
            metadatas=all_metadatas,
            ids=all_ids,
        )

        logger.info(
            "인덱싱 완료: channel=%s, type=%s, chunks=%d",
            channel_id,
            source_type,
            len(all_chunks),
        )
        return len(all_chunks)

    def clear_channel(self, channel_id: str) -> None:
        """채널의 인덱스를 삭제합니다."""
        client = self._get_client()
        collection_name = self._config.collection_name(channel_id)
        try:
            client.delete_collection(name=collection_name)
            logger.info("인덱스 삭제: channel=%s", channel_id)
        except Exception:
            logger.debug("삭제할 컬렉션이 없습니다: %s", collection_name)

    def index_channel(self, channel_id: str, channel_path: Path) -> int:
        """채널의 모든 자료를 인덱싱합니다 (brand_guide + sources).

        Returns:
            총 인덱싱된 청크 수
        """
        total = 0

        guide_path = channel_path / "brand_guide.yaml"
        if guide_path.exists():
            total += self.index_brand_guide(channel_id, guide_path)

        sources_dir = channel_path / "sources"
        if sources_dir.exists():
            total += self.index_sources(channel_id, sources_dir)

        return total

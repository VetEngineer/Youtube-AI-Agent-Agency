"""ChromaDB에서 관련 컨텍스트를 검색하는 모듈."""

from __future__ import annotations

import logging

from .config import RAGConfig

logger = logging.getLogger(__name__)


class BrandRetriever:
    """벡터 스토리지에서 브랜드 관련 컨텍스트를 검색합니다."""

    def __init__(self, config: RAGConfig | None = None) -> None:
        self._config = config or RAGConfig()
        self._client = None

    def _get_client(self):
        """ChromaDB 클라이언트를 lazy 초기화합니다."""
        if self._client is not None:
            return self._client

        import chromadb

        self._client = chromadb.PersistentClient(
            path=str(self._config.persist_path),
        )
        return self._client

    def retrieve(self, channel_id: str, query: str, top_k: int | None = None) -> list[str]:
        """쿼리에 관련된 문서 청크를 검색합니다.

        Args:
            channel_id: 채널 ID
            query: 검색 쿼리
            top_k: 반환할 결과 수 (기본값: config.rag_top_k)

        Returns:
            관련 문서 청크 리스트
        """
        k = top_k or self._config.rag_top_k
        collection_name = self._config.collection_name(channel_id)

        try:
            client = self._get_client()
            collection = client.get_collection(name=collection_name)

            results = collection.query(
                query_texts=[query],
                n_results=k,
            )

            documents = results.get("documents", [[]])[0]
            logger.info(
                "RAG 검색: channel=%s, query=%s..., results=%d",
                channel_id,
                query[:50],
                len(documents),
            )
            return documents

        except Exception:
            logger.debug("RAG 검색 실패 (컬렉션 없음 등): channel=%s", channel_id)
            return []

    def retrieve_with_metadata(
        self,
        channel_id: str,
        query: str,
        top_k: int | None = None,
    ) -> list[dict[str, str]]:
        """메타데이터와 함께 관련 문서를 검색합니다.

        Returns:
            [{"content": ..., "source_type": ..., "source_name": ...}, ...]
        """
        k = top_k or self._config.rag_top_k
        collection_name = self._config.collection_name(channel_id)

        try:
            client = self._get_client()
            collection = client.get_collection(name=collection_name)

            results = collection.query(
                query_texts=[query],
                n_results=k,
            )

            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]

            return [
                {
                    "content": doc,
                    "source_type": meta.get("source_type", ""),
                    "source_name": meta.get("source_name", ""),
                }
                for doc, meta in zip(documents, metadatas)
            ]

        except Exception:
            logger.debug("RAG 검색 실패: channel=%s", channel_id)
            return []

    def build_context(self, channel_id: str, query: str, top_k: int | None = None) -> str:
        """검색 결과를 프롬프트에 삽입할 컨텍스트 문자열로 조합합니다.

        Returns:
            포맷된 컨텍스트 문자열 (결과 없으면 빈 문자열)
        """
        results = self.retrieve_with_metadata(channel_id, query, top_k)
        if not results:
            return ""

        sections = []
        for r in results:
            source = r.get("source_name", "unknown")
            content = r.get("content", "")
            sections.append(f"[{source}]\n{content}")

        return "\n\n---\n\n".join(sections)

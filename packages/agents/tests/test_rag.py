"""브랜드 리서치 RAG 테스트."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.brand_researcher.collector import CollectedSource, CollectionResult

# ChromaDB 임베딩 모델이 로컬에 준비되어 있어야 실제 인덱싱/검색 테스트 가능
_CHROMA_MODEL_READY = os.path.exists(
    os.path.expanduser("~/.cache/chroma/onnx_models/all-MiniLM-L6-v2/onnx/model.onnx")
)
requires_chroma_model = pytest.mark.skipif(
    not _CHROMA_MODEL_READY,
    reason="ChromaDB ONNX 임베딩 모델이 로컬에 없음 (CI에서 실행)",
)


# ============================================
# RAG Config 테스트
# ============================================


class TestRAGConfig:
    """RAG 설정 테스트."""

    def test_기본_설정_값(self):
        from src.brand_researcher.rag.config import RAGConfig

        config = RAGConfig()
        assert config.rag_enabled is False
        assert config.rag_chunk_size == 500
        assert config.rag_chunk_overlap == 50
        assert config.rag_top_k == 5

    def test_환경변수_오버라이드(self, monkeypatch):
        from src.brand_researcher.rag.config import RAGConfig

        monkeypatch.setenv("RAG_ENABLED", "true")
        monkeypatch.setenv("RAG_CHUNK_SIZE", "1000")
        monkeypatch.setenv("RAG_TOP_K", "10")

        config = RAGConfig()
        assert config.rag_enabled is True
        assert config.rag_chunk_size == 1000
        assert config.rag_top_k == 10

    def test_컬렉션_이름_생성(self):
        from src.brand_researcher.rag.config import RAGConfig

        config = RAGConfig()
        assert config.collection_name("test-channel") == "yaa_brand_test-channel"

    def test_persist_path(self):
        from src.brand_researcher.rag.config import RAGConfig

        config = RAGConfig(rag_persist_dir="/tmp/test-chroma")
        assert config.persist_path == Path("/tmp/test-chroma")


# ============================================
# Indexer 테스트 (유닛)
# ============================================


class TestBrandIndexer:
    """BrandIndexer 유닛 테스트."""

    def test_텍스트_청킹(self):
        from src.brand_researcher.rag.config import RAGConfig
        from src.brand_researcher.rag.indexer import BrandIndexer

        config = RAGConfig(rag_chunk_size=10, rag_chunk_overlap=3)
        indexer = BrandIndexer(config)

        text = "abcdefghijklmnopqrstuvwxyz"
        chunks = indexer._chunk_text(text)
        assert len(chunks) > 0
        assert chunks[0] == "abcdefghij"

    def test_빈_텍스트_청킹(self):
        from src.brand_researcher.rag.config import RAGConfig
        from src.brand_researcher.rag.indexer import BrandIndexer

        config = RAGConfig()
        indexer = BrandIndexer(config)
        assert indexer._chunk_text("") == []
        assert indexer._chunk_text("   ") == []

    def test_존재하지_않는_파일_인덱싱(self, tmp_path):
        from src.brand_researcher.rag.config import RAGConfig
        from src.brand_researcher.rag.indexer import BrandIndexer

        config = RAGConfig(rag_persist_dir=str(tmp_path / "chroma"))
        indexer = BrandIndexer(config)

        count = indexer.index_brand_guide("test-ch", tmp_path / "nonexistent.yaml")
        assert count == 0

    def test_존재하지_않는_채널_삭제(self, tmp_path):
        from src.brand_researcher.rag.config import RAGConfig
        from src.brand_researcher.rag.indexer import BrandIndexer

        config = RAGConfig(rag_persist_dir=str(tmp_path / "chroma"))
        indexer = BrandIndexer(config)
        indexer.clear_channel("nonexistent")  # 에러 없이 통과해야 함


# ============================================
# Indexer + Retriever 통합 테스트 (ChromaDB 모델 필요)
# ============================================


@requires_chroma_model
class TestBrandIndexerIntegration:
    """ChromaDB 실제 인덱싱 테스트 (임베딩 모델 필요)."""

    def test_brand_guide_인덱싱(self, tmp_path):
        from src.brand_researcher.rag.config import RAGConfig
        from src.brand_researcher.rag.indexer import BrandIndexer

        chroma_dir = tmp_path / "chroma"
        config = RAGConfig(rag_persist_dir=str(chroma_dir), rag_chunk_size=50)
        indexer = BrandIndexer(config)

        guide_path = tmp_path / "brand_guide.yaml"
        guide_path.write_text(
            "brand:\n  name: 테스트\n  positioning: 프리미엄\n" * 5,
            encoding="utf-8",
        )

        count = indexer.index_brand_guide("test-ch", guide_path)
        assert count > 0

    def test_sources_디렉토리_인덱싱(self, tmp_path):
        from src.brand_researcher.rag.config import RAGConfig
        from src.brand_researcher.rag.indexer import BrandIndexer

        chroma_dir = tmp_path / "chroma"
        config = RAGConfig(rag_persist_dir=str(chroma_dir), rag_chunk_size=50)
        indexer = BrandIndexer(config)

        sources_dir = tmp_path / "sources"
        sources_dir.mkdir()
        (sources_dir / "doc1.txt").write_text("테스트 문서 " * 20, encoding="utf-8")

        count = indexer.index_sources("test-ch", sources_dir)
        assert count > 0

    def test_인덱싱_후_검색(self, tmp_path):
        from src.brand_researcher.rag.config import RAGConfig
        from src.brand_researcher.rag.indexer import BrandIndexer
        from src.brand_researcher.rag.retriever import BrandRetriever

        chroma_dir = tmp_path / "chroma"
        config = RAGConfig(rag_persist_dir=str(chroma_dir), rag_chunk_size=100)

        indexer = BrandIndexer(config)
        guide = tmp_path / "guide.yaml"
        guide.write_text(
            "brand:\n  name: 딥퓨어캐터리\n  positioning: 프리미엄 고양이\n" * 3,
            encoding="utf-8",
        )
        indexer.index_brand_guide("deepure", guide)

        retriever = BrandRetriever(config)
        results = retriever.retrieve("deepure", "고양이")
        assert len(results) > 0


# ============================================
# Retriever 유닛 테스트
# ============================================


class TestBrandRetriever:
    """BrandRetriever 유닛 테스트."""

    def test_컬렉션_없을때_빈_결과(self, tmp_path):
        from src.brand_researcher.rag.config import RAGConfig
        from src.brand_researcher.rag.retriever import BrandRetriever

        config = RAGConfig(rag_persist_dir=str(tmp_path / "chroma"))
        retriever = BrandRetriever(config)

        results = retriever.retrieve("nonexistent", "query")
        assert results == []

    def test_빈_컬렉션_컨텍스트_빌드(self, tmp_path):
        from src.brand_researcher.rag.config import RAGConfig
        from src.brand_researcher.rag.retriever import BrandRetriever

        config = RAGConfig(rag_persist_dir=str(tmp_path / "chroma"))
        retriever = BrandRetriever(config)
        context = retriever.build_context("nonexistent", "query")
        assert context == ""


# ============================================
# Agent RAG 통합 테스트 (모킹)
# ============================================


class TestAgentRAGIntegration:
    """BrandResearcherAgent RAG 통합 테스트."""

    def test_rag_비활성화시_원본_유지(self):
        from src.brand_researcher.agent import BrandResearcherAgent
        from src.shared.config import ChannelRegistry

        mock_llm = MagicMock()
        mock_registry = MagicMock(spec=ChannelRegistry)
        agent = BrandResearcherAgent(
            llm=mock_llm, registry=mock_registry, rag_enabled=False,
        )

        original = CollectionResult(
            sources=[CollectedSource(title="test", content="content")],
            errors=[],
        )

        result = agent._enrich_with_rag(original, "ch1", "brand")
        assert len(result.sources) == 1

    def test_rag_활성화시_retriever_없으면_원본_유지(self):
        from src.brand_researcher.agent import BrandResearcherAgent
        from src.shared.config import ChannelRegistry

        mock_llm = MagicMock()
        mock_registry = MagicMock(spec=ChannelRegistry)
        agent = BrandResearcherAgent(
            llm=mock_llm, registry=mock_registry, rag_enabled=True,
        )

        original = CollectionResult(
            sources=[CollectedSource(title="test", content="content")],
            errors=[],
        )

        # retriever가 없거나 결과가 없으면 원본 그대로
        result = agent._enrich_with_rag(original, "ch1", "brand")
        assert len(result.sources) >= 1

    @patch("src.brand_researcher.agent.BrandResearcherAgent._get_rag_retriever")
    def test_rag_활성화시_컨텍스트_추가(self, mock_get_retriever):
        from src.brand_researcher.agent import BrandResearcherAgent
        from src.shared.config import ChannelRegistry

        mock_retriever = MagicMock()
        mock_retriever.retrieve_with_metadata.return_value = [
            {
                "content": "RAG 결과 내용",
                "source_type": "brand_guide",
                "source_name": "guide.yaml",
            },
        ]
        mock_get_retriever.return_value = mock_retriever

        mock_llm = MagicMock()
        mock_registry = MagicMock(spec=ChannelRegistry)
        agent = BrandResearcherAgent(
            llm=mock_llm, registry=mock_registry, rag_enabled=True,
        )

        original = CollectionResult(
            sources=[CollectedSource(title="web", content="웹 검색 결과")],
            errors=[],
        )

        result = agent._enrich_with_rag(original, "ch1", "brand")
        assert len(result.sources) == 2  # 원본 1 + RAG 1
        assert result.sources[1].source_type == "rag"
        assert "[RAG]" in result.sources[1].title

    @patch("src.brand_researcher.agent.BrandResearcherAgent._get_rag_retriever")
    def test_rag_검색_결과_없으면_원본_유지(self, mock_get_retriever):
        from src.brand_researcher.agent import BrandResearcherAgent
        from src.shared.config import ChannelRegistry

        mock_retriever = MagicMock()
        mock_retriever.retrieve_with_metadata.return_value = []
        mock_get_retriever.return_value = mock_retriever

        mock_llm = MagicMock()
        mock_registry = MagicMock(spec=ChannelRegistry)
        agent = BrandResearcherAgent(
            llm=mock_llm, registry=mock_registry, rag_enabled=True,
        )

        original = CollectionResult(
            sources=[CollectedSource(title="test", content="content")],
            errors=[],
        )

        result = agent._enrich_with_rag(original, "ch1", "brand")
        assert len(result.sources) == 1

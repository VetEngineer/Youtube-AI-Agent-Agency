"""브랜드 관련 자료 수집기.

웹 검색(Tavily), SNS 채널 정보, 로컬 문서를 수집합니다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import httpx

from src.shared.config import AppSettings


@dataclass(frozen=True)
class CollectedSource:
    """수집된 개별 자료."""

    title: str
    content: str
    url: str = ""
    source_type: str = "web"


@dataclass
class CollectionResult:
    """수집 결과 전체."""

    sources: list[CollectedSource] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def combined_text(self) -> str:
        return "\n\n---\n\n".join(f"[{s.source_type}] {s.title}\n{s.content}" for s in self.sources)


class BrandCollector:
    """브랜드 관련 자료를 수집하는 클래스."""

    def __init__(self, settings: AppSettings | None = None) -> None:
        self._settings = settings or AppSettings()

    async def search_web(self, query: str, max_results: int = 5) -> list[CollectedSource]:
        """Tavily API를 사용하여 웹 검색을 수행합니다."""
        if not self._settings.tavily_api_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    headers={
                        "Authorization": f"Bearer {self._settings.tavily_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "query": query,
                        "max_results": max_results,
                        "include_answer": False,
                        "include_raw_content": False,
                    },
                )
                response.raise_for_status()
                data = response.json()

            return [
                CollectedSource(
                    title=result.get("title", ""),
                    content=result.get("content", ""),
                    url=result.get("url", ""),
                    source_type="web",
                )
                for result in data.get("results", [])
            ]
        except Exception as e:
            return [
                CollectedSource(
                    title="검색 오류",
                    content=f"웹 검색 실패: {e}",
                    source_type="error",
                )
            ]

    def load_local_documents(self, sources_dir: Path) -> list[CollectedSource]:
        """로컬 sources/ 디렉토리에서 문서를 로드합니다."""
        results: list[CollectedSource] = []

        if not sources_dir.exists():
            return results

        for file_path in sorted(sources_dir.iterdir()):
            if file_path.suffix in (".txt", ".md"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    results.append(
                        CollectedSource(
                            title=file_path.stem,
                            content=content,
                            source_type="document",
                        )
                    )
                except Exception:
                    continue
            elif file_path.suffix == ".yaml":
                try:
                    content = file_path.read_text(encoding="utf-8")
                    results.append(
                        CollectedSource(
                            title=file_path.stem,
                            content=content,
                            source_type="yaml",
                        )
                    )
                except Exception:
                    continue

        return results

    def load_link_list(self, sources_dir: Path) -> list[str]:
        """sources/links.txt에서 URL 목록을 로드합니다."""
        links_file = sources_dir / "links.txt"
        if not links_file.exists():
            return []

        content = links_file.read_text(encoding="utf-8")
        return [
            line.strip()
            for line in content.splitlines()
            if line.strip() and not line.startswith("#")
        ]

    async def collect_all(
        self,
        brand_name: str,
        channel_sources_dir: Path | None = None,
        additional_queries: list[str] | None = None,
    ) -> CollectionResult:
        """모든 소스에서 브랜드 자료를 수집합니다."""
        result = CollectionResult()

        # 1. 로컬 문서 로드
        if channel_sources_dir:
            local_docs = self.load_local_documents(channel_sources_dir)
            result.sources.extend(local_docs)

        # 2. 웹 검색
        queries = [
            f"{brand_name} 브랜드 소개",
            f"{brand_name} 후기 리뷰",
        ]
        if additional_queries:
            queries.extend(additional_queries)

        for query in queries:
            try:
                web_results = await self.search_web(query)
                result.sources.extend(web_results)
            except Exception as e:
                result.errors.append(f"검색 실패 ({query}): {e}")

        return result

"""CLI 엔트리포인트 - YouTube AI Agent Agency.

명령어:
  youtube-agent run --channel <id> --topic <topic> [--dry-run]
  youtube-agent channels list
  youtube-agent channels create <id>
  youtube-agent brand-research --channel <id> --brand <name>
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from typing import TYPE_CHECKING

from yaa_core.shared.config import AppSettings, ChannelRegistry
from yaa_core.shared.llm_clients import UsageCollector

if TYPE_CHECKING:
    from yaa_agents.orchestrator import AgentRegistry

logger = logging.getLogger(__name__)


def _setup_logging(level: str = "INFO") -> None:
    """로깅을 설정합니다."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _build_agent_registry(
    settings: AppSettings,
    collector: UsageCollector | None = None,
) -> AgentRegistry:
    """에이전트 레지스트리를 빌드합니다.

    LLM 클라이언트 및 각 에이전트 인스턴스를 생성하여
    AgentRegistry에 등록합니다.
    """
    from yaa_agents.brand_researcher import BrandResearcherAgent
    from yaa_agents.media_editor import MediaEditorAgent
    from yaa_agents.media_generator import (
        ElevenLabsVoiceGenerator,
        MediaGeneratorAgent,
        MidjourneyGenerator,
    )
    from yaa_agents.orchestrator import AgentRegistry
    from yaa_agents.publisher import PublisherAgent, YouTubeUploader
    from yaa_agents.script_writer import ScriptWriterAgent
    from yaa_agents.seo_optimizer import SEOOptimizerAgent
    from yaa_core.shared.llm_clients import create_anthropic_client, create_openai_client

    channel_registry = ChannelRegistry(settings.channels_dir)

    br_callbacks = [collector.create_callback("brand_researcher", "openai")] if collector else None
    sw_callbacks = [collector.create_callback("script_writer", "anthropic")] if collector else None
    seo_callbacks = [collector.create_callback("seo_optimizer", "openai")] if collector else None

    brand_researcher_llm = create_openai_client(callbacks=br_callbacks)
    anthropic_llm = create_anthropic_client(callbacks=sw_callbacks)
    seo_llm = create_openai_client(callbacks=seo_callbacks)

    brand_researcher = BrandResearcherAgent(
        llm=brand_researcher_llm,
        registry=channel_registry,
        rag_enabled=settings.rag_enabled,
    )
    script_writer = ScriptWriterAgent(llm=anthropic_llm)
    seo_optimizer = SEOOptimizerAgent(llm=seo_llm)
    media_editor = MediaEditorAgent()

    voice_generator = ElevenLabsVoiceGenerator(api_key=settings.elevenlabs_api_key)
    image_generator = MidjourneyGenerator(api_key=settings.midjourney_api_key)
    media_generator = MediaGeneratorAgent(
        voice_generator=voice_generator,
        image_generator=image_generator,
    )

    uploader = YouTubeUploader(
        client_id=settings.youtube_client_id,
        client_secret=settings.youtube_client_secret,
    )
    publisher = PublisherAgent(uploader=uploader)

    return AgentRegistry(
        brand_researcher=brand_researcher,
        script_writer=script_writer,
        media_generator=media_generator,
        media_editor=media_editor,
        seo_optimizer=seo_optimizer,
        publisher=publisher,
        channel_registry=channel_registry,
    )


def _log_usage_summary(collector: UsageCollector) -> None:
    """수집된 LLM 사용량 요약을 로그로 출력합니다."""
    if not collector.events:
        return

    total_cost = sum(e["cost_usd"] for e in collector.events)
    total_tokens = sum(e["total_tokens"] for e in collector.events)

    logger.info(
        "LLM 사용량: calls=%d, tokens=%d, cost=$%.6f",
        len(collector.events),
        total_tokens,
        total_cost,
    )
    for event in collector.events:
        logger.debug(
            "  %s (%s/%s): tokens=%d, cost=$%.6f",
            event["agent"],
            event["provider"],
            event["model"],
            event["total_tokens"],
            event["cost_usd"],
        )

    if collector.failed_count > 0:
        logger.warning(
            "사용량 추적 실패: %d건",
            collector.failed_count,
        )


async def _cmd_run(args: argparse.Namespace) -> int:
    """파이프라인 실행."""
    from yaa_agents.orchestrator import compile_pipeline, create_initial_state

    settings = AppSettings()
    _setup_logging(settings.log_level)

    logger.info("파이프라인 시작: channel=%s, topic=%s", args.channel, args.topic)

    collector = UsageCollector()
    agent_registry = _build_agent_registry(settings, collector=collector)
    pipeline = compile_pipeline(agent_registry)

    initial_state = create_initial_state(
        channel_id=args.channel,
        topic=args.topic,
        dry_run=args.dry_run,
    )

    try:
        final_state = await pipeline.ainvoke(initial_state)

        _log_usage_summary(collector)

        status = final_state.get("status")
        if status and status.value == "failed":
            logger.error("파이프라인 실패: %s", final_state.get("errors"))
            return 1

        logger.info("파이프라인 완료: status=%s", status)
        if args.dry_run:
            logger.info("dry-run 모드: 실제 업로드를 건너뛰었습니다")

        return 0
    except Exception as exc:
        _log_usage_summary(collector)
        logger.exception("파이프라인 실행 중 에러: %s", exc)
        return 1


async def _cmd_channels_list(_args: argparse.Namespace) -> int:
    """채널 목록 조회."""
    settings = AppSettings()
    registry = ChannelRegistry(settings.channels_dir)
    channels = registry.list_channels()

    if not channels:
        print("등록된 채널이 없습니다.")
        return 0

    print(f"등록된 채널 ({len(channels)}개):")
    for channel_id in channels:
        try:
            config = registry.load_settings(channel_id)
            has_guide = registry.has_brand_guide(channel_id)
            mark = "\u2713" if has_guide else "\u2717"
            print(f"  [{mark}] {channel_id} - {config.channel.name}")
        except Exception as exc:
            print(f"  [?] {channel_id} - 설정 로드 실패: {exc}")

    return 0


async def _cmd_channels_create(args: argparse.Namespace) -> int:
    """새 채널 생성."""
    settings = AppSettings()
    registry = ChannelRegistry(settings.channels_dir)

    try:
        channel_path = registry.create_channel_from_template(args.channel_id)
        print(f"채널 생성 완료: {channel_path}")
        print("다음 파일을 수정하세요:")
        print(f"  - {channel_path / 'config.yaml'}")
        return 0
    except FileExistsError:
        print(f"채널이 이미 존재합니다: {args.channel_id}")
        return 1


async def _cmd_rag_index(args: argparse.Namespace) -> int:
    """RAG 인덱싱 실행."""
    from yaa_agents.brand_researcher.rag import BrandIndexer, RAGConfig

    settings = AppSettings()
    _setup_logging(settings.log_level)

    registry = ChannelRegistry(settings.channels_dir)

    try:
        channel_path = registry.get_channel_path(args.channel_id)
    except FileNotFoundError:
        print(f"채널을 찾을 수 없습니다: {args.channel_id}")
        return 1

    config = RAGConfig()
    indexer = BrandIndexer(config)

    try:
        n = indexer.index_channel(args.channel_id, channel_path)
        print(f"Indexed {n} chunks")
        return 0
    except Exception as exc:
        logger.exception("RAG 인덱싱 실패: %s", exc)
        return 1


async def _cmd_brand_research(args: argparse.Namespace) -> int:
    """브랜드 리서치 실행."""
    from yaa_agents.brand_researcher import BrandResearcherAgent
    from yaa_core.shared.llm_clients import create_openai_client

    settings = AppSettings()
    _setup_logging(settings.log_level)

    registry = ChannelRegistry(settings.channels_dir)
    llm = create_openai_client()

    agent = BrandResearcherAgent(llm=llm, registry=registry)

    try:
        guide, saved_path = await agent.research_and_save(
            channel_id=args.channel,
            brand_name=args.brand,
        )
        logger.info("브랜드 리서치 완료")
        print(f"브랜드 가이드 생성: {saved_path}")
        return 0
    except Exception as exc:
        logger.exception("브랜드 리서치 실패: %s", exc)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    """CLI 파서를 빌드합니다."""
    parser = argparse.ArgumentParser(
        prog="youtube-agent",
        description="YouTube AI Agent Agency CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="사용 가능한 명령어")

    # run
    run_parser = subparsers.add_parser("run", help="파이프라인 실행")
    run_parser.add_argument("--channel", required=True, help="채널 ID")
    run_parser.add_argument("--topic", required=True, help="콘텐츠 주제")
    run_parser.add_argument("--dry-run", action="store_true", help="실제 업로드 건너뜀")

    # channels
    channels_parser = subparsers.add_parser("channels", help="채널 관리")
    channels_sub = channels_parser.add_subparsers(dest="channels_command")

    channels_sub.add_parser("list", help="채널 목록 조회")

    create_parser = channels_sub.add_parser("create", help="새 채널 생성")
    create_parser.add_argument("channel_id", help="채널 ID")

    # brand-research
    research_parser = subparsers.add_parser("brand-research", help="브랜드 리서치 실행")
    research_parser.add_argument("--channel", required=True, help="채널 ID")
    research_parser.add_argument("--brand", required=True, help="브랜드명")

    # rag-index
    rag_parser = subparsers.add_parser("rag-index", help="채널 브랜드 자료 RAG 인덱싱")
    rag_parser.add_argument("--channel-id", required=True, help="채널 ID")

    return parser


def main() -> int:
    """CLI 메인 엔트리포인트."""
    parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "run":
        return asyncio.run(_cmd_run(args))

    if args.command == "channels":
        if not getattr(args, "channels_command", None):
            parser.parse_args(["channels", "--help"])
            return 1
        if args.channels_command == "list":
            return asyncio.run(_cmd_channels_list(args))
        if args.channels_command == "create":
            return asyncio.run(_cmd_channels_create(args))

    if args.command == "brand-research":
        return asyncio.run(_cmd_brand_research(args))

    if args.command == "rag-index":
        return asyncio.run(_cmd_rag_index(args))

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

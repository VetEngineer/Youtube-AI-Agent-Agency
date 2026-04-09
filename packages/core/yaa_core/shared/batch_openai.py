"""OpenAI Batch API 클라이언트.

비실시간 파이프라인에서 50% 비용 절감을 위해 Batch API를 사용합니다.
단일 요청도 배치로 제출 가능 (할인은 동일하게 적용).

사용법:
    result = await batch_chat_completion(
        system_prompt="...",
        user_prompt="...",
        api_key="sk-...",
        model="gpt-4o",
    )
"""

from __future__ import annotations

import asyncio
import json
import logging
import tempfile
import time
import uuid
from pathlib import Path

import openai

logger = logging.getLogger(__name__)

_POLL_INTERVAL_SECONDS = 5
_DEFAULT_TIMEOUT_SECONDS = 600  # 10분


async def batch_chat_completion(
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    model: str = "gpt-4o",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    timeout: int = _DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """OpenAI Batch API로 chat completion을 실행합니다.

    Args:
        system_prompt: 시스템 프롬프트
        user_prompt: 사용자 프롬프트
        api_key: OpenAI API 키
        model: 사용할 모델
        temperature: 온도
        max_tokens: 최대 출력 토큰
        timeout: 배치 완료 대기 최대 시간 (초)

    Returns:
        LLM 응답 텍스트

    Raises:
        TimeoutError: 배치가 timeout 내에 완료되지 않은 경우
        RuntimeError: 배치 실행 실패
    """
    # AsyncOpenAI를 사용하여 이벤트 루프 차단 방지 (#70)
    client = openai.AsyncOpenAI(api_key=api_key)
    request_id = f"req-{uuid.uuid4().hex[:12]}"

    # 1. JSONL 파일 생성
    request_body = {
        "custom_id": request_id,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
    }

    jsonl_path: Path | None = None
    try:
        # 임시 파일 생성을 try 블록 안에서 수행하여 누수 방지 (#70)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps(request_body) + "\n")
            jsonl_path = Path(f.name)

        # 2. 파일 업로드
        with open(jsonl_path, "rb") as f:
            uploaded = await client.files.create(file=f, purpose="batch")
        logger.info("배치 파일 업로드 완료: file_id=%s", uploaded.id)

        # 3. 배치 생성
        batch = await client.batches.create(
            input_file_id=uploaded.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )
        logger.info("배치 생성 완료: batch_id=%s", batch.id)

        # 4. 폴링 — time.monotonic()으로 정확한 타임아웃 추적 (#70)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            batch = await client.batches.retrieve(batch.id)
            if batch.status == "completed":
                break
            if batch.status in ("failed", "expired", "cancelled"):
                raise RuntimeError(f"배치 실패: status={batch.status}, errors={batch.errors}")
            await asyncio.sleep(_POLL_INTERVAL_SECONDS)

        if batch.status != "completed":
            # 타임아웃 시 배치 취소 시도
            try:
                await client.batches.cancel(batch.id)
            except Exception:
                pass
            raise TimeoutError(f"배치가 {timeout}초 내에 완료되지 않았습니다: batch_id={batch.id}")

        # 5. 결과 다운로드
        if not batch.output_file_id:
            raise RuntimeError("배치 출력 파일이 없습니다")

        output = await client.files.content(batch.output_file_id)
        result_line = output.text.strip().split("\n")[0]
        result = json.loads(result_line)

        # 6. 응답 추출
        response_body = result.get("response", {}).get("body", {})
        choices = response_body.get("choices", [])
        if not choices:
            raise RuntimeError("배치 응답에 choices가 없습니다")

        content = choices[0].get("message", {}).get("content", "")

        # 사용량 로깅
        usage = response_body.get("usage", {})
        logger.info(
            "배치 완료: model=%s, prompt=%d, completion=%d (50%% 할인 적용)",
            model,
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
        )

        return content

    finally:
        if jsonl_path is not None:
            jsonl_path.unlink(missing_ok=True)

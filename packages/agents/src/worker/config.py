"""워커 및 Redis 설정."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class WorkerSettings(BaseSettings):
    """Arq 워커 설정."""

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    worker_max_jobs: int = 5
    worker_job_timeout: int = 1800  # 30분
    worker_queue_name: str = "yaa:pipeline"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "env_prefix": ""}

    @property
    def redis_settings(self):
        """Arq RedisSettings 객체를 반환합니다."""
        from arq.connections import RedisSettings as ArqRedisSettings

        return ArqRedisSettings(
            host=self.redis_host,
            port=self.redis_port,
            database=self.redis_db,
            password=self.redis_password or None,
        )


def get_worker_settings() -> WorkerSettings:
    """워커 설정 싱글턴을 반환합니다."""
    return WorkerSettings()

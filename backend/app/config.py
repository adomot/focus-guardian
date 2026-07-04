from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """環境変数による実行時設定。ローカル開発はすべてフェイク実装で動く既定値にする。"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    google_cloud_project: str = ""
    google_cloud_location: str = "asia-northeast1"

    repository_backend: Literal["memory", "firestore"] = "memory"
    agents_backend: Literal["fake", "adk"] = "fake"
    assets_backend: Literal["fake", "gcs"] = "fake"
    speaker_adapter: Literal["null", "voicemonkey"] = "null"

    judge_model: str = "gemini-2.5-flash-lite"
    structuring_model: str = "gemini-2.5-flash-lite"

    voicemonkey_token: str = ""
    voicemonkey_device: str = ""
    voicemonkey_base_url: str = "https://api-v3.voicemonkey.io"

    gcs_assets_bucket: str = ""

    capture_interval_seconds: int = 60
    consecutive_threshold: int = 2
    confidence_threshold: float = 0.7
    frame_rate_limit_per_minute: int = 10
    max_frame_bytes: int = 1_000_000

    static_dir: str = "static"


@lru_cache
def get_settings() -> Settings:
    return Settings()

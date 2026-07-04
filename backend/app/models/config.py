from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DetectionCondition(BaseModel):
    """自由入力の悪習慣を画像判定可能な形に構造化したもの (要件 1.8)"""

    habit_label: str
    visual_cues: list[str] = Field(min_length=1)
    judge_hint: str


class Notification(BaseModel):
    """悪習慣ごとの通知設定。audio_url は介入時にそのまま再生される公開 URL"""

    method: Literal["bgm", "speech"]
    bgm_track_id: str | None = None
    phrase: str | None = None
    audio_url: str


class Habit(BaseModel):
    habit_id: str
    label: str
    visual_cues: list[str]
    judge_hint: str
    notification: Notification


class MonitoringConfig(BaseModel):
    """ヒアリング完了時に保存される監視設定 (要件 1.9)"""

    config_id: str
    goal: str
    habits: list[Habit]
    created_at: datetime

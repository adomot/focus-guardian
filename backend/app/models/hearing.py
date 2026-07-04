from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel

from app.models.config import Notification


class HearingStep(StrEnum):
    GOAL = "GOAL"
    HABIT = "HABIT"
    NOTIFY_TYPE = "NOTIFY_TYPE"
    BGM_SELECT = "BGM_SELECT"
    PHRASE = "PHRASE"
    MORE_HABITS = "MORE_HABITS"
    DONE = "DONE"


class Choice(BaseModel):
    choice_id: str
    label: str


class UserInput(BaseModel):
    text: str | None = None
    choice_id: str | None = None


class HearingTurn(BaseModel):
    """API がフロントに返す1ターン。フロントはこれをそのまま描画する (要件 1.3, 1.6)"""

    hearing_id: str
    bot_message: str
    input_mode: Literal["free_text", "choices"]
    choices: list[Choice] | None = None
    done: bool = False
    config_id: str | None = None


class DraftHabit(BaseModel):
    """構造化済みだが通知設定が未確定の悪習慣"""

    label: str
    visual_cues: list[str]
    judge_hint: str
    notification: Notification | None = None


class HearingState(BaseModel):
    """ヒアリング進行状態 (Firestore hearings コレクション)"""

    hearing_id: str
    step: HearingStep
    goal: str | None = None
    habits: list[DraftHabit] = []
    current_habit: DraftHabit | None = None
    updated_at: datetime

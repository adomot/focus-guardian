from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class Frame(BaseModel):
    """判定対象の1枚。リクエストスコープ外に持ち出さない (要件 7.1)"""

    jpeg_bytes: bytes
    captured_at: datetime


class JudgmentState(StrEnum):
    FOCUSED = "focused"
    HABIT = "habit"
    ABSENT = "absent"


class JudgmentResult(BaseModel):
    state: JudgmentState
    habit_id: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class JudgmentRecord(BaseModel):
    """判定履歴 (sessions/{id}/judgments)。画像は含めない (要件 3.2, 7.1)"""

    ts: datetime
    state: str  # JudgmentState または "error"
    habit_id: str | None = None
    confidence: float | None = None
    reason: str | None = None
    error: str | None = None


class HabitPhase(StrEnum):
    ARMED = "armed"
    FIRED = "fired"


class HabitState(BaseModel):
    phase: HabitPhase = HabitPhase.ARMED
    consecutive_count: int = 0


class SessionCounters(BaseModel):
    frames: int = 0
    focused: int = 0
    habit_detected: int = 0
    interventions: int = 0


class SessionState(BaseModel):
    session_id: str
    config_id: str
    status: Literal["active", "ended"] = "active"
    started_at: datetime
    ended_at: datetime | None = None
    habit_states: dict[str, HabitState] = {}
    pending_evaluation: str | None = None  # 直前の intervention_id
    counters: SessionCounters = SessionCounters()


class InterventionDirective(BaseModel):
    """介入指示。delivered_by=browser のときフロントが再生する (要件 4.8)"""

    intervention_id: str
    habit_id: str
    method: Literal["bgm", "speech"]
    audio_url: str
    delivered_by: Literal["speaker", "browser"]


class InterventionRecord(BaseModel):
    """介入履歴 (sessions/{id}/interventions) (要件 4.10, 5.2)"""

    intervention_id: str
    ts: datetime
    habit_id: str
    method: Literal["bgm", "speech"]
    delivered_by: Literal["speaker", "browser"]
    result: Literal["returned", "not_returned", "unknown"] = "unknown"


class FrameResult(BaseModel):
    judgment: JudgmentRecord
    intervention: InterventionDirective | None = None


class SessionSummary(BaseModel):
    session_id: str
    goal: str
    started_at: datetime
    ended_at: datetime
    focused_minutes: float
    frames: int
    habit_detected: int
    interventions: int
    returned_count: int
    habit_breakdown: dict[str, int] = {}

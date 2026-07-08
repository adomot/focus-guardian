"""Gemini 呼び出しエージェントを日次上限でラップするデコレータ。

上限到達時は RateLimitExceededError を送出する。これは AgentError の
サブクラスなので、判定 (次周期で再試行) とヒアリング (同一質問の再提示)
の既存エラー経路でそのまま処理される。
"""

from datetime import UTC, datetime

from app.agents.base import (
    JudgeAgentPort,
    RateLimitExceededError,
    StructuringAgentPort,
)
from app.models.config import DetectionCondition, MonitoringConfig
from app.models.monitoring import Frame, JudgmentResult
from app.services.rate_limiter import GlobalRateLimiter


class RateLimitedStructuringAgent:
    def __init__(self, inner: StructuringAgentPort, limiter: GlobalRateLimiter) -> None:
        self._inner = inner
        self._limiter = limiter

    async def structure_habit(self, raw_text: str) -> DetectionCondition:
        if not await self._limiter.try_consume(datetime.now(UTC)):
            raise RateLimitExceededError("Gemini の日次呼び出し上限に達しました")
        return await self._inner.structure_habit(raw_text)


class RateLimitedJudgeAgent:
    def __init__(self, inner: JudgeAgentPort, limiter: GlobalRateLimiter) -> None:
        self._inner = inner
        self._limiter = limiter

    async def judge(self, frame: Frame, config: MonitoringConfig) -> JudgmentResult:
        if not await self._limiter.try_consume(datetime.now(UTC)):
            raise RateLimitExceededError("Gemini の日次呼び出し上限に達しました")
        return await self._inner.judge(frame, config)

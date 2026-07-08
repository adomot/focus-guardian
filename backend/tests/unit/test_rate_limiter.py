"""Gemini 日次上限のテスト (コスト暴走の防波堤)"""

from datetime import UTC, datetime

import pytest

from app.agents.base import RateLimitExceededError
from app.agents.fake import FakeJudgeAgent, FakeStructuringAgent
from app.agents.rate_limited import RateLimitedJudgeAgent, RateLimitedStructuringAgent
from app.models.config import Habit, MonitoringConfig, Notification
from app.models.monitoring import Frame
from app.services.rate_limiter import MemoryDailyRateLimiter, day_key


def at(iso: str) -> datetime:
    return datetime.fromisoformat(iso).replace(tzinfo=UTC)


class TestDayKey:
    def test_jst_offset_applied(self):
        # UTC 2026-07-09 15:30 = JST 2026-07-10 00:30
        assert day_key(at("2026-07-09T15:30:00")) == "gemini-2026-07-10"
        # UTC 2026-07-09 14:30 = JST 2026-07-09 23:30
        assert day_key(at("2026-07-09T14:30:00")) == "gemini-2026-07-09"


class TestMemoryLimiter:
    async def test_allows_up_to_limit_then_blocks(self):
        limiter = MemoryDailyRateLimiter(limit=3)
        now = at("2026-07-09T01:00:00")
        assert [await limiter.try_consume(now) for _ in range(4)] == [True, True, True, False]

    async def test_resets_on_new_day(self):
        limiter = MemoryDailyRateLimiter(limit=1)
        assert await limiter.try_consume(at("2026-07-09T01:00:00")) is True
        assert await limiter.try_consume(at("2026-07-09T05:00:00")) is False
        # 翌 JST 日 → リセット
        assert await limiter.try_consume(at("2026-07-09T15:30:00")) is True


class TestWrappers:
    def _config(self) -> MonitoringConfig:
        return MonitoringConfig(
            config_id="c",
            goal="g",
            habits=[
                Habit(
                    habit_id="habit_1",
                    label="スマホ",
                    visual_cues=["x"],
                    judge_hint="y",
                    notification=Notification(method="bgm", bgm_track_id="focus", audio_url="u"),
                )
            ],
            created_at=datetime.now(UTC),
        )

    async def test_judge_wrapper_raises_after_limit(self):
        limiter = MemoryDailyRateLimiter(limit=1)
        agent = RateLimitedJudgeAgent(FakeJudgeAgent(), limiter)
        frame = Frame(jpeg_bytes=b"\xff\xd8\xff" + b"\x00" * 8, captured_at=datetime.now(UTC))
        await agent.judge(frame, self._config())
        with pytest.raises(RateLimitExceededError):
            await agent.judge(frame, self._config())

    async def test_structuring_wrapper_raises_after_limit(self):
        limiter = MemoryDailyRateLimiter(limit=1)
        agent = RateLimitedStructuringAgent(FakeStructuringAgent(), limiter)
        await agent.structure_habit("スマホをいじる")
        with pytest.raises(RateLimitExceededError):
            await agent.structure_habit("居眠り")

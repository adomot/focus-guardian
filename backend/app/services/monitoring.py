"""フレーム受信 → 判定 → 介入 → 記録の1サイクル統括 (要件 3.1, 3.2, 3.5, 7.1)。

画像はこのモジュールのリクエストスコープでのみ扱い、永続化もログ出力もしない。
"""

import logging
from datetime import UTC, datetime

from app.adapters.camera import WebcamPushSource
from app.adapters.speaker import SpeakerAdapter
from app.agents.base import AgentError, JudgeAgentPort
from app.models.config import MonitoringConfig
from app.models.monitoring import (
    Frame,
    FrameResult,
    InterventionRecord,
    JudgmentRecord,
    SessionState,
)
from app.repositories.base import ConfigRepository, SessionRepository
from app.services.intervention_policy import InterventionPolicy

logger = logging.getLogger(__name__)


class SessionNotActiveError(Exception):
    pass


class SessionNotFoundError(Exception):
    pass


class MonitoringService:
    def __init__(
        self,
        sessions: SessionRepository,
        configs: ConfigRepository,
        camera: WebcamPushSource,
        judge: JudgeAgentPort,
        speaker: SpeakerAdapter,
        policy: InterventionPolicy,
    ) -> None:
        self._sessions = sessions
        self._configs = configs
        self._camera = camera
        self._judge = judge
        self._speaker = speaker
        self._policy = policy

    async def process_frame(self, session_id: str, frame: Frame) -> FrameResult:
        session = await self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        if session.status != "active":
            raise SessionNotActiveError(session_id)
        config = await self._configs.get(session.config_id)
        if config is None:
            raise SessionNotFoundError(f"config missing: {session.config_id}")

        self._camera.push(session_id, frame)
        try:
            latest = await self._camera.get_latest_frame(session_id)
            assert latest is not None
            return await self._run_cycle(session, config, latest)
        finally:
            self._camera.discard(session_id)  # 画像をリクエストスコープ外に残さない (7.1)

    async def _run_cycle(
        self, session: SessionState, config: MonitoringConfig, frame: Frame
    ) -> FrameResult:
        now = datetime.now(UTC)
        try:
            judgment = await self._judge.judge(frame, config)
        except AgentError as exc:
            # 判定失敗はエラーとして記録し、次フレームで自然に再試行される (要件 3.5)
            logger.warning("judgment failed: %s", exc)
            record = JudgmentRecord(ts=now, state="error", error=str(exc)[:500])
            await self._sessions.append_judgment(session.session_id, record)
            await self._sessions.update(session.session_id, self._increment_frames)
            return FrameResult(judgment=record)

        record = JudgmentRecord(
            ts=now,
            state=judgment.state.value,
            habit_id=judgment.habit_id,
            confidence=judgment.confidence,
            reason=judgment.reason,
        )
        await self._sessions.append_judgment(session.session_id, record)

        decision = self._policy.decide(session, config, judgment)

        directive = decision.directive
        if directive is not None:
            result = await self._speaker.play(directive.audio_url)
            delivered_by = "speaker" if result.ok else "browser"  # 要件 4.8
            directive = directive.model_copy(update={"delivered_by": delivered_by})
            await self._sessions.append_intervention(
                session.session_id,
                InterventionRecord(
                    intervention_id=directive.intervention_id,
                    ts=now,
                    habit_id=directive.habit_id,
                    method=directive.method,
                    delivered_by=delivered_by,
                ),
            )

        if decision.evaluation_result and decision.evaluated_intervention_id:
            await self._sessions.update_intervention_result(
                session.session_id,
                decision.evaluated_intervention_id,
                decision.evaluation_result,
            )

        def apply_policy_state(current: SessionState) -> SessionState:
            updated = decision.session.model_copy(deep=True)
            updated.counters.frames = current.counters.frames + 1
            return updated

        await self._sessions.update(session.session_id, apply_policy_state)
        return FrameResult(judgment=record, intervention=directive)

    @staticmethod
    def _increment_frames(current: SessionState) -> SessionState:
        current.counters.frames += 1
        return current

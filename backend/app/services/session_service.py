"""セッションのライフサイクル管理とサマリー集計 (要件 6.1, 6.3)"""

import uuid
from datetime import UTC, datetime

from app.models.monitoring import SessionState, SessionSummary
from app.repositories.base import ConfigRepository, SessionRepository
from app.services.monitoring import SessionNotFoundError


class SessionService:
    def __init__(
        self,
        sessions: SessionRepository,
        configs: ConfigRepository,
        capture_interval_seconds: int,
    ) -> None:
        self._sessions = sessions
        self._configs = configs
        self._interval = capture_interval_seconds

    async def start(self, config_id: str | None) -> SessionState:
        config = (
            await self._configs.get(config_id) if config_id else await self._configs.get_latest()
        )
        if config is None:
            raise SessionNotFoundError("monitoring config not found")
        session = SessionState(
            session_id=uuid.uuid4().hex,  # 推測困難な ID (セキュリティ考慮事項)
            config_id=config.config_id,
            started_at=datetime.now(UTC),
        )
        await self._sessions.create(session)
        return session

    async def get(self, session_id: str) -> SessionState:
        session = await self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        return session

    async def end(self, session_id: str) -> SessionSummary:
        def mark_ended(current: SessionState) -> SessionState:
            current.status = "ended"
            current.ended_at = datetime.now(UTC)
            return current

        try:
            session = await self._sessions.update(session_id, mark_ended)
        except KeyError as exc:
            raise SessionNotFoundError(session_id) from exc
        return await self._summarize(session)

    async def _summarize(self, session: SessionState) -> SessionSummary:
        config = await self._configs.get(session.config_id)
        judgments = await self._sessions.list_judgments(session.session_id)
        interventions = await self._sessions.list_interventions(session.session_id)

        habit_breakdown: dict[str, int] = {}
        label_by_id = {h.habit_id: h.label for h in (config.habits if config else [])}
        for record in judgments:
            if record.state == "habit" and record.habit_id:
                label = label_by_id.get(record.habit_id, record.habit_id)
                habit_breakdown[label] = habit_breakdown.get(label, 0) + 1

        # 集中時間はキャプチャ間隔 × focused 判定数の近似値 (design.md 参照)
        focused_minutes = round(session.counters.focused * self._interval / 60, 1)
        returned_count = sum(1 for r in interventions if r.result == "returned")

        return SessionSummary(
            session_id=session.session_id,
            goal=config.goal if config else "",
            started_at=session.started_at,
            ended_at=session.ended_at or datetime.now(UTC),
            focused_minutes=focused_minutes,
            frames=session.counters.frames,
            habit_detected=session.counters.habit_detected,
            interventions=session.counters.interventions,
            returned_count=returned_count,
            habit_breakdown=habit_breakdown,
        )

import asyncio
from collections.abc import Callable

from app.models.config import MonitoringConfig
from app.models.hearing import HearingState
from app.models.monitoring import InterventionRecord, JudgmentRecord, SessionState


class MemoryConfigRepository:
    def __init__(self) -> None:
        self._items: dict[str, MonitoringConfig] = {}

    async def save(self, config: MonitoringConfig) -> None:
        self._items[config.config_id] = config.model_copy(deep=True)

    async def get(self, config_id: str) -> MonitoringConfig | None:
        item = self._items.get(config_id)
        return item.model_copy(deep=True) if item else None

    async def get_latest(self) -> MonitoringConfig | None:
        if not self._items:
            return None
        latest = max(self._items.values(), key=lambda c: c.created_at)
        return latest.model_copy(deep=True)


class MemoryHearingRepository:
    def __init__(self) -> None:
        self._items: dict[str, HearingState] = {}

    async def save(self, state: HearingState) -> None:
        self._items[state.hearing_id] = state.model_copy(deep=True)

    async def get(self, hearing_id: str) -> HearingState | None:
        item = self._items.get(hearing_id)
        return item.model_copy(deep=True) if item else None


class MemorySessionRepository:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}
        self._judgments: dict[str, list[JudgmentRecord]] = {}
        self._interventions: dict[str, list[InterventionRecord]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def _lock(self, session_id: str) -> asyncio.Lock:
        return self._locks.setdefault(session_id, asyncio.Lock())

    async def create(self, session: SessionState) -> None:
        self._sessions[session.session_id] = session.model_copy(deep=True)
        self._judgments[session.session_id] = []
        self._interventions[session.session_id] = []

    async def get(self, session_id: str) -> SessionState | None:
        item = self._sessions.get(session_id)
        return item.model_copy(deep=True) if item else None

    async def update(
        self, session_id: str, mutate: Callable[[SessionState], SessionState]
    ) -> SessionState:
        async with self._lock(session_id):
            current = self._sessions.get(session_id)
            if current is None:
                raise KeyError(session_id)
            updated = mutate(current.model_copy(deep=True))
            self._sessions[session_id] = updated.model_copy(deep=True)
            return updated

    async def append_judgment(self, session_id: str, record: JudgmentRecord) -> None:
        self._judgments.setdefault(session_id, []).append(record.model_copy(deep=True))

    async def list_judgments(self, session_id: str) -> list[JudgmentRecord]:
        return [r.model_copy(deep=True) for r in self._judgments.get(session_id, [])]

    async def append_intervention(self, session_id: str, record: InterventionRecord) -> None:
        self._interventions.setdefault(session_id, []).append(record.model_copy(deep=True))

    async def update_intervention_result(
        self, session_id: str, intervention_id: str, result: str
    ) -> None:
        records = self._interventions.get(session_id, [])
        updated = [
            r.model_copy(update={"result": result})
            if r.intervention_id == intervention_id
            else r
            for r in records
        ]
        self._interventions[session_id] = updated

    async def list_interventions(self, session_id: str) -> list[InterventionRecord]:
        return [r.model_copy(deep=True) for r in self._interventions.get(session_id, [])]

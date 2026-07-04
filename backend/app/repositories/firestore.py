from collections.abc import Callable

from google.cloud import firestore

from app.models.config import MonitoringConfig
from app.models.hearing import HearingState
from app.models.monitoring import InterventionRecord, JudgmentRecord, SessionState

CONFIGS = "configs"
HEARINGS = "hearings"
SESSIONS = "sessions"
JUDGMENTS = "judgments"
INTERVENTIONS = "interventions"


class FirestoreConfigRepository:
    def __init__(self, client: firestore.AsyncClient) -> None:
        self._db = client

    async def save(self, config: MonitoringConfig) -> None:
        doc = config.model_dump(mode="json")
        await self._db.collection(CONFIGS).document(config.config_id).set(doc)

    async def get(self, config_id: str) -> MonitoringConfig | None:
        snap = await self._db.collection(CONFIGS).document(config_id).get()
        return MonitoringConfig.model_validate(snap.to_dict()) if snap.exists else None

    async def get_latest(self) -> MonitoringConfig | None:
        query = (
            self._db.collection(CONFIGS)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(1)
        )
        async for snap in query.stream():
            return MonitoringConfig.model_validate(snap.to_dict())
        return None


class FirestoreHearingRepository:
    def __init__(self, client: firestore.AsyncClient) -> None:
        self._db = client

    async def save(self, state: HearingState) -> None:
        doc = state.model_dump(mode="json")
        await self._db.collection(HEARINGS).document(state.hearing_id).set(doc)

    async def get(self, hearing_id: str) -> HearingState | None:
        snap = await self._db.collection(HEARINGS).document(hearing_id).get()
        return HearingState.model_validate(snap.to_dict()) if snap.exists else None


class FirestoreSessionRepository:
    def __init__(self, client: firestore.AsyncClient) -> None:
        self._db = client

    def _doc(self, session_id: str):
        return self._db.collection(SESSIONS).document(session_id)

    async def create(self, session: SessionState) -> None:
        await self._doc(session.session_id).set(session.model_dump(mode="json"))

    async def get(self, session_id: str) -> SessionState | None:
        snap = await self._doc(session_id).get()
        return SessionState.model_validate(snap.to_dict()) if snap.exists else None

    async def update(
        self, session_id: str, mutate: Callable[[SessionState], SessionState]
    ) -> SessionState:
        transaction = self._db.transaction()
        doc_ref = self._doc(session_id)

        @firestore.async_transactional
        async def _run(tx: firestore.AsyncTransaction) -> SessionState:
            snap = await doc_ref.get(transaction=tx)
            if not snap.exists:
                raise KeyError(session_id)
            current = SessionState.model_validate(snap.to_dict())
            updated = mutate(current)
            tx.set(doc_ref, updated.model_dump(mode="json"))
            return updated

        return await _run(transaction)

    async def append_judgment(self, session_id: str, record: JudgmentRecord) -> None:
        await self._doc(session_id).collection(JUDGMENTS).add(record.model_dump(mode="json"))

    async def list_judgments(self, session_id: str) -> list[JudgmentRecord]:
        query = self._doc(session_id).collection(JUDGMENTS).order_by("ts")
        return [JudgmentRecord.model_validate(s.to_dict()) async for s in query.stream()]

    async def append_intervention(self, session_id: str, record: InterventionRecord) -> None:
        await (
            self._doc(session_id)
            .collection(INTERVENTIONS)
            .document(record.intervention_id)
            .set(record.model_dump(mode="json"))
        )

    async def update_intervention_result(
        self, session_id: str, intervention_id: str, result: str
    ) -> None:
        await (
            self._doc(session_id)
            .collection(INTERVENTIONS)
            .document(intervention_id)
            .update({"result": result})
        )

    async def list_interventions(self, session_id: str) -> list[InterventionRecord]:
        query = self._doc(session_id).collection(INTERVENTIONS).order_by("ts")
        return [InterventionRecord.model_validate(s.to_dict()) async for s in query.stream()]

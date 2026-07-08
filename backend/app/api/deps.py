"""依存の組み立て。設定に応じてフェイク/実サービスを注入する (design.md 技術スタック参照)"""

import time
from dataclasses import dataclass, field

from app.adapters.camera import WebcamPushSource
from app.adapters.speaker import NullSpeaker, SpeakerAdapter, VoiceMonkeySpeaker
from app.agents.base import JudgeAgentPort, StructuringAgentPort
from app.agents.rate_limited import RateLimitedJudgeAgent, RateLimitedStructuringAgent
from app.config import Settings
from app.repositories.base import ConfigRepository
from app.services.hearing_flow import HearingFlowService
from app.services.intervention_policy import InterventionPolicy
from app.services.monitoring import MonitoringService
from app.services.rate_limiter import (
    FirestoreDailyRateLimiter,
    GlobalRateLimiter,
    MemoryDailyRateLimiter,
)
from app.services.session_service import SessionService
from app.services.speech_assets import (
    FakeSpeechAssetService,
    GcsSpeechAssetService,
    SpeechAssetService,
)


class FrameRateLimiter:
    """セッションあたりの簡易レート制限 (セキュリティ考慮事項)"""

    def __init__(self, limit_per_minute: int) -> None:
        self._limit = limit_per_minute
        self._buckets: dict[str, list[float]] = {}

    def allow(self, session_id: str) -> bool:
        now = time.monotonic()
        bucket = [t for t in self._buckets.get(session_id, []) if now - t < 60]
        if len(bucket) >= self._limit:
            self._buckets[session_id] = bucket
            return False
        bucket.append(now)
        self._buckets[session_id] = bucket
        return True


@dataclass
class Container:
    settings: Settings
    hearing_flow: HearingFlowService
    monitoring: MonitoringService
    session_service: SessionService
    configs: ConfigRepository
    rate_limiter: FrameRateLimiter = field(init=False)

    def __post_init__(self) -> None:
        self.rate_limiter = FrameRateLimiter(self.settings.frame_rate_limit_per_minute)


def _build_firestore_client(settings: Settings):
    if settings.repository_backend != "firestore":
        return None
    from google.cloud import firestore

    return firestore.AsyncClient(project=settings.google_cloud_project or None)


def _build_repositories(settings: Settings, client):
    if client is not None:
        from app.repositories.firestore import (
            FirestoreConfigRepository,
            FirestoreHearingRepository,
            FirestoreSessionRepository,
        )

        return (
            FirestoreConfigRepository(client),
            FirestoreHearingRepository(client),
            FirestoreSessionRepository(client),
        )
    from app.repositories.memory import (
        MemoryConfigRepository,
        MemoryHearingRepository,
        MemorySessionRepository,
    )

    return MemoryConfigRepository(), MemoryHearingRepository(), MemorySessionRepository()


def _build_rate_limiter(settings: Settings, client) -> GlobalRateLimiter:
    if client is not None:
        return FirestoreDailyRateLimiter(client, settings.gemini_daily_limit)
    return MemoryDailyRateLimiter(settings.gemini_daily_limit)


def _build_agents(settings: Settings) -> tuple[StructuringAgentPort, JudgeAgentPort]:
    if settings.agents_backend == "adk":
        from app.agents.adk_agents import AdkJudgeAgent, AdkStructuringAgent

        return (
            AdkStructuringAgent(settings.structuring_model),
            AdkJudgeAgent(settings.judge_model),
        )
    from app.agents.fake import FakeJudgeAgent, FakeStructuringAgent

    return FakeStructuringAgent(), FakeJudgeAgent()


def _build_assets(settings: Settings) -> SpeechAssetService:
    if settings.assets_backend == "gcs":
        return GcsSpeechAssetService(settings.gcs_assets_bucket)
    return FakeSpeechAssetService()


def _build_speaker(settings: Settings) -> SpeakerAdapter:
    if settings.speaker_adapter == "voicemonkey":
        return VoiceMonkeySpeaker(
            base_url=settings.voicemonkey_base_url,
            token=settings.voicemonkey_token,
            device=settings.voicemonkey_device,
        )
    return NullSpeaker()


def build_container(settings: Settings) -> Container:
    client = _build_firestore_client(settings)
    configs, hearings, sessions = _build_repositories(settings, client)
    limiter = _build_rate_limiter(settings, client)
    structuring, judge = _build_agents(settings)
    structuring = RateLimitedStructuringAgent(structuring, limiter)
    judge = RateLimitedJudgeAgent(judge, limiter)
    assets = _build_assets(settings)
    speaker = _build_speaker(settings)
    camera = WebcamPushSource()
    policy = InterventionPolicy(
        consecutive_threshold=settings.consecutive_threshold,
        confidence_threshold=settings.confidence_threshold,
    )

    return Container(
        settings=settings,
        hearing_flow=HearingFlowService(hearings, configs, structuring, assets),
        monitoring=MonitoringService(sessions, configs, camera, judge, speaker, policy),
        session_service=SessionService(sessions, configs, settings.capture_interval_seconds),
        configs=configs,
    )

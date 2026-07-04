import asyncio
import logging
from typing import Literal, Protocol

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SpeakerResult(BaseModel):
    ok: bool
    error: Literal["throttled", "quota_exceeded", "unreachable", "config"] | None = None


class SpeakerAdapter(Protocol):
    """出力デバイスの共通インターフェース (要件 4.6, 4.9)。

    実装: VoiceMonkeySpeaker (Alexa) / NullSpeaker (ブラウザのみ運用) /
    将来の GoogleCastSpeaker。
    """

    async def play(self, audio_url: str) -> SpeakerResult: ...


class NullSpeaker:
    """外部スピーカーなし。常に失敗を返し、ブラウザフォールバックに委ねる"""

    async def play(self, audio_url: str) -> SpeakerResult:
        return SpeakerResult(ok=False, error="config")


class VoiceMonkeySpeaker:
    """Voice Monkey API v3 経由で Echo に音声を再生させる (要件 4.7)。

    429 は短いバックオフで1回だけ再試行し、失敗は即座に返して
    ブラウザフォールバックへ切り替えさせる (介入の即時性を優先)。
    """

    RETRY_DELAY_SECONDS = 2.0

    def __init__(
        self,
        base_url: str,
        token: str,
        device: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._device = device
        self._transport = transport  # テスト用に差し替え可能

    async def play(self, audio_url: str) -> SpeakerResult:
        if not self._token or not self._device:
            return SpeakerResult(ok=False, error="config")
        result = await self._announce(audio_url)
        if result.error == "throttled":
            await asyncio.sleep(self.RETRY_DELAY_SECONDS)
            result = await self._announce(audio_url)
        return result

    async def _announce(self, audio_url: str) -> SpeakerResult:
        try:
            async with httpx.AsyncClient(timeout=10.0, transport=self._transport) as client:
                response = await client.post(
                    f"{self._base_url}/announce",
                    headers={"Authorization": f"Bearer {self._token}"},
                    json={"device": self._device, "audio": audio_url},
                )
        except httpx.HTTPError as exc:
            logger.warning("Voice Monkey unreachable: %s", exc)
            return SpeakerResult(ok=False, error="unreachable")

        if response.status_code == 200:
            return SpeakerResult(ok=True)
        if response.status_code == 429:
            body = response.text
            error = "quota_exceeded" if "QUOTA" in body.upper() else "throttled"
            logger.warning("Voice Monkey throttled/quota: %s", body[:200])
            return SpeakerResult(ok=False, error=error)
        logger.warning(
            "Voice Monkey error: status=%s body=%s", response.status_code, response.text[:200]
        )
        return SpeakerResult(ok=False, error="unreachable")

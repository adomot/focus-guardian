import logging
import uuid
from typing import Protocol

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BgmTrack(BaseModel):
    track_id: str
    label: str
    object_name: str


# BGM 固定ラインアップ (要件 1.4)。音源ファイルはアセットバケットに配置する
BGM_CATALOG: list[BgmTrack] = [
    BgmTrack(track_id="focus", label="集中できるBGM", object_name="bgm/focus.mp3"),
    BgmTrack(track_id="nature", label="自然音", object_name="bgm/nature.mp3"),
    BgmTrack(track_id="uptempo", label="アップテンポ", object_name="bgm/uptempo.mp3"),
]


def get_bgm_track(track_id: str) -> BgmTrack | None:
    return next((t for t in BGM_CATALOG if t.track_id == track_id), None)


class SpeechAssetService(Protocol):
    """通知音声アセットの解決と生成 (要件 4.2, 4.3)"""

    def bgm_url(self, track_id: str) -> str: ...
    async def synthesize_phrase(self, phrase: str) -> str: ...


class FakeSpeechAssetService:
    """ローカル開発用。実音声は生成せずプレースホルダ URL を返す"""

    def __init__(self, base_url: str = "https://assets.invalid") -> None:
        self._base_url = base_url

    def bgm_url(self, track_id: str) -> str:
        track = get_bgm_track(track_id)
        if track is None:
            raise ValueError(f"unknown bgm track: {track_id}")
        return f"{self._base_url}/{track.object_name}"

    async def synthesize_phrase(self, phrase: str) -> str:
        return f"{self._base_url}/phrases/fake-{uuid.uuid4().hex}.mp3"


class GcsSpeechAssetService:
    """Cloud TTS で日本語フレーズを MP3 化し、公開バケットに保存する。

    オブジェクト名は推測困難な UUID (セキュリティ考慮事項参照)。
    """

    VOICE_NAME = "ja-JP-Neural2-B"

    def __init__(self, bucket_name: str) -> None:
        self._bucket_name = bucket_name

    def bgm_url(self, track_id: str) -> str:
        track = get_bgm_track(track_id)
        if track is None:
            raise ValueError(f"unknown bgm track: {track_id}")
        return f"https://storage.googleapis.com/{self._bucket_name}/{track.object_name}"

    async def synthesize_phrase(self, phrase: str) -> str:
        from google.cloud import storage, texttospeech

        client = texttospeech.TextToSpeechAsyncClient()
        response = await client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=phrase),
            voice=texttospeech.VoiceSelectionParams(
                language_code="ja-JP", name=self.VOICE_NAME
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            ),
        )

        object_name = f"phrases/{uuid.uuid4().hex}.mp3"
        storage_client = storage.Client()
        bucket = storage_client.bucket(self._bucket_name)
        blob = bucket.blob(object_name)
        blob.upload_from_string(response.audio_content, content_type="audio/mpeg")
        logger.info("synthesized phrase asset: %s", object_name)
        return f"https://storage.googleapis.com/{self._bucket_name}/{object_name}"

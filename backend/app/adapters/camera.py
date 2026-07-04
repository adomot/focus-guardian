from typing import Protocol

from app.models.monitoring import Frame


class CameraSource(Protocol):
    """カメラ入力源の共通インターフェース (要件 2.3)。

    将来の NestCamSource (SDM API / WebRTC) も同じ契約を実装する。
    """

    async def get_latest_frame(self, session_id: str) -> Frame | None: ...


class WebcamPushSource:
    """ブラウザから POST されたフレームを保持する Web カメラ実装 (要件 2.2)。

    画像はメモリ上にのみ存在し、pop 後は参照が残らない (要件 7.1)。
    Cloud Run は max-instances=1 で運用する前提。
    """

    def __init__(self) -> None:
        self._latest: dict[str, Frame] = {}

    def push(self, session_id: str, frame: Frame) -> None:
        self._latest[session_id] = frame

    async def get_latest_frame(self, session_id: str) -> Frame | None:
        return self._latest.get(session_id)

    def discard(self, session_id: str) -> None:
        self._latest.pop(session_id, None)

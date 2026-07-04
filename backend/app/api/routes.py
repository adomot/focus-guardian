from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, UploadFile

from app.api.deps import Container
from app.models.hearing import HearingTurn, UserInput
from app.models.monitoring import Frame, FrameResult, SessionState, SessionSummary
from app.services.hearing_flow import HearingNotFoundError
from app.services.monitoring import SessionNotActiveError, SessionNotFoundError

JPEG_MAGIC = b"\xff\xd8\xff"


def _container(request: Request) -> Container:
    return request.app.state.container


def _error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


router = APIRouter(prefix="/api")


@router.post("/hearing", response_model=HearingTurn)
async def start_hearing(request: Request) -> HearingTurn:
    return await _container(request).hearing_flow.start()


@router.post("/hearing/{hearing_id}/reply", response_model=HearingTurn)
async def reply_hearing(hearing_id: str, user_input: UserInput, request: Request) -> HearingTurn:
    try:
        return await _container(request).hearing_flow.reply(hearing_id, user_input)
    except HearingNotFoundError:
        raise _error(404, "hearing_not_found", "ヒアリングが見つかりません") from None


@router.get("/configs/latest")
async def get_latest_config(request: Request) -> dict:
    config = await _container(request).configs.get_latest()
    if config is None:
        raise _error(404, "config_not_found", "監視設定がまだありません")
    return {
        "config_id": config.config_id,
        "goal": config.goal,
        "habits": [
            {
                "habit_id": h.habit_id,
                "label": h.label,
                "method": h.notification.method,
                "phrase": h.notification.phrase,
                "audio_url": h.notification.audio_url,
            }
            for h in config.habits
        ],
    }


@router.post("/sessions", response_model=SessionState)
async def start_session(request: Request, body: dict | None = None) -> SessionState:
    config_id = (body or {}).get("config_id")
    try:
        return await _container(request).session_service.start(config_id)
    except SessionNotFoundError:
        raise _error(404, "config_not_found", "監視設定がまだありません") from None


@router.get("/sessions/{session_id}", response_model=SessionState)
async def get_session(session_id: str, request: Request) -> SessionState:
    try:
        return await _container(request).session_service.get(session_id)
    except SessionNotFoundError:
        raise _error(404, "session_not_found", "セッションが見つかりません") from None


@router.post("/sessions/{session_id}/end", response_model=SessionSummary)
async def end_session(session_id: str, request: Request) -> SessionSummary:
    try:
        return await _container(request).session_service.end(session_id)
    except SessionNotFoundError:
        raise _error(404, "session_not_found", "セッションが見つかりません") from None


@router.post("/sessions/{session_id}/frames", response_model=FrameResult)
async def post_frame(session_id: str, request: Request, image: UploadFile) -> FrameResult:
    container = _container(request)
    if not container.rate_limiter.allow(session_id):
        raise _error(429, "rate_limited", "フレーム送信が多すぎます")

    data = await image.read()
    if len(data) > container.settings.max_frame_bytes:
        raise _error(413, "frame_too_large", "画像サイズが上限を超えています")
    if not data.startswith(JPEG_MAGIC):
        raise _error(400, "invalid_frame", "JPEG 画像を送信してください")

    frame = Frame(jpeg_bytes=data, captured_at=datetime.now(UTC))
    try:
        return await container.monitoring.process_frame(session_id, frame)
    except SessionNotFoundError:
        raise _error(404, "session_not_found", "セッションが見つかりません") from None
    except SessionNotActiveError:
        raise _error(409, "session_ended", "セッションは終了しています") from None

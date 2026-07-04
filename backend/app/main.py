import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.deps import build_container
from app.api.routes import router
from app.config import Settings, get_settings

logging.basicConfig(level=logging.INFO, format='{"level": "%(levelname)s", "msg": %(message)r}')


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Focus Guardian", docs_url=None, redoc_url=None)
    app.state.container = build_container(settings)
    app.include_router(router)

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict) and "code" in detail:
            body = {"error": detail}
        else:
            body = {"error": {"code": "http_error", "message": str(detail)}}
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logging.getLogger(__name__).exception("unhandled error")
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal", "message": "サーバエラーが発生しました"}},
        )

    # /healthz は Google Frontend の予約パスで Cloud Run に届かないため /api/health を使う
    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    static_dir = Path(settings.static_dir)
    if static_dir.is_dir():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app


app = create_app()

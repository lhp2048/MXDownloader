import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.api.playlists import router as playlists_router
from app.api.routes import router as api_router
from app.api.files import router as files_router
from app.api.web import router as web_router
from app.config import settings
from app.db import init_db
from app.services.playlist_service import playlist_service
from app.services.task_manager import task_manager

WEB_DIR = Path(__file__).resolve().parent / "web"


class Utf8HTMLMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        content_type = response.headers.get("content-type", "")
        if content_type.startswith("text/html") and "charset" not in content_type.lower():
            response.headers["content-type"] = "text/html; charset=utf-8"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await playlist_service.ensure_default_playlist()
    await playlist_service.sync_default_from_tasks()
    await task_manager.recover_on_startup()
    await task_manager.start_polling()
    yield
    await task_manager.stop_polling()


app = FastAPI(
    title="MyDownloader",
    description="Local download service with yt-dlp, aria2, and Alist",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(Utf8HTMLMiddleware)

app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")
app.include_router(files_router)
app.include_router(playlists_router)
app.include_router(api_router)
app.include_router(web_router)


def run() -> None:
    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=False,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    run()

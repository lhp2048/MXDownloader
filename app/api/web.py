from pathlib import Path

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.services.engine_status import get_all_engine_status, get_system_summary
from app.services.file_manager import get_public_base_url, list_directory
from app.services.task_manager import task_manager

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))


def _format_filesize(value: int) -> str:
    if not value or value <= 0:
        return "-"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{value} B"


templates.env.filters["filesize"] = _format_filesize

router = APIRouter(tags=["web"])


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    tasks = await task_manager.list_tasks(tab="active")
    counts = await task_manager.get_task_counts()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"tasks": tasks, "counts": counts, "tab": "active", "settings": settings},
    )


@router.get("/partials/tasks", response_class=HTMLResponse)
async def tasks_partial(
    request: Request,
    tab: str = Query("active"),
) -> HTMLResponse:
    tasks = await task_manager.list_tasks(tab=tab)
    return templates.TemplateResponse(
        request,
        "partials/task_table.html",
        {"tasks": tasks, "tab": tab},
    )


@router.get("/partials/task-counts", response_class=HTMLResponse)
async def task_counts_partial(request: Request) -> HTMLResponse:
    counts = await task_manager.get_task_counts()
    return templates.TemplateResponse(
        request,
        "partials/task_tabs.html",
        {"counts": counts, "tab": request.query_params.get("tab", "active")},
    )


@router.get("/components", response_class=HTMLResponse)
async def components_page(request: Request) -> HTMLResponse:
    summary = await get_system_summary()
    engines = await get_all_engine_status()
    return templates.TemplateResponse(
        request,
        "components.html",
        {"summary": summary, "engines": engines, "settings": settings},
    )


@router.get("/partials/components", response_class=HTMLResponse)
async def components_partial(request: Request) -> HTMLResponse:
    engines = await get_all_engine_status()
    return templates.TemplateResponse(
        request,
        "partials/components_status.html",
        {"engines": engines},
    )



@router.get("/files", response_class=HTMLResponse)
async def files_page(request: Request) -> HTMLResponse:
    base = get_public_base_url(str(request.base_url).rstrip("/"))
    listing = list_directory("", base)
    listing_json = listing.model_dump_json()
    return templates.TemplateResponse(
        request,
        "files.html",
        {
            "listing": listing,
            "listing_json": listing_json,
            "settings": settings,
        },
    )


@router.get("/media", response_class=HTMLResponse)
async def media_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "media.html",
        {"settings": settings},
    )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request) -> HTMLResponse:
    base_url = str(request.base_url).rstrip("/")
    return templates.TemplateResponse(
        request,
        "settings.html",
        {"settings": settings, "base_url": base_url},
    )


@router.get("/health")
async def health() -> dict:
    summary = await get_system_summary()
    engines_map = {e["name"]: e["available"] for e in summary["engines"]}
    return {
        "status": "ok",
        "engines": engines_map,
        "engines_available": summary["engines_available"],
        "engines_total": summary["engines_total"],
    }

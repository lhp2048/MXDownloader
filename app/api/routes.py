from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.config import AppSettings, load_settings, save_settings
from app.models.task import SettingsUpdate, TaskCreate, TaskResponse
from app.services.engine_status import (
    get_all_engine_status,
    get_engine_status,
    get_system_summary,
    status_to_dict,
)
from app.services.task_manager import task_manager

router = APIRouter(prefix="/api/v1", tags=["api"])


def verify_api_key(request: Request) -> None:
    s = load_settings()
    api_key = s.server.api_key
    if api_key:
        header = request.headers.get("X-API-Key", "")
        if header != api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")


@router.post("/downloads", response_model=TaskResponse, dependencies=[Depends(verify_api_key)])
async def create_download(data: TaskCreate) -> TaskResponse:
    try:
        return await task_manager.create_task(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks", response_model=list[TaskResponse], dependencies=[Depends(verify_api_key)])
async def list_tasks(
    status: Optional[str] = Query(None),
    tab: Optional[str] = Query(None),
) -> list[TaskResponse]:
    return await task_manager.list_tasks(status=status, tab=tab)


@router.get("/tasks/counts", dependencies=[Depends(verify_api_key)])
async def task_counts() -> dict:
    return await task_manager.get_task_counts()


@router.delete("/tasks/{task_id}", dependencies=[Depends(verify_api_key)])
async def delete_task(
    task_id: int,
    delete_file: bool = Query(False),
) -> dict:
    try:
        await task_manager.delete_task(task_id, delete_file=delete_file)
        return {"ok": True, "id": task_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskResponse, dependencies=[Depends(verify_api_key)])
async def get_task(task_id: int) -> TaskResponse:
    try:
        return await task_manager.get_task(task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/tasks/{task_id}/pause",
    response_model=TaskResponse,
    dependencies=[Depends(verify_api_key)],
)
async def pause_task(task_id: int) -> TaskResponse:
    try:
        return await task_manager.pause_task(task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/tasks/{task_id}/cancel",
    response_model=TaskResponse,
    dependencies=[Depends(verify_api_key)],
)
async def cancel_task(task_id: int) -> TaskResponse:
    try:
        return await task_manager.cancel_task(task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/settings", dependencies=[Depends(verify_api_key)])
async def get_settings() -> dict:
    s = load_settings()
    return {
        "server": s.server.model_dump(),
        "download": s.download.model_dump(),
        "files": s.files.model_dump(),
        "engines": {
            "ytdlp_path": s.engines.ytdlp_path,
            "aria2": s.engines.aria2.model_dump(),
            "alist": s.engines.alist.model_dump(),
        },
    }


@router.put("/settings", dependencies=[Depends(verify_api_key)])
async def update_settings(data: SettingsUpdate) -> dict:
    s = load_settings()
    if data.server:
        for k, v in data.server.items():
            if hasattr(s.server, k):
                setattr(s.server, k, v)
    if data.download:
        for k, v in data.download.items():
            if hasattr(s.download, k):
                setattr(s.download, k, v)
    if data.files:
        for k, v in data.files.items():
            if hasattr(s.files, k):
                setattr(s.files, k, v)
    if data.engines:
        if "ytdlp_path" in data.engines:
            s.engines.ytdlp_path = data.engines["ytdlp_path"]
        if "aria2" in data.engines:
            for k, v in data.engines["aria2"].items():
                if hasattr(s.engines.aria2, k):
                    setattr(s.engines.aria2, k, v)
        if "alist" in data.engines:
            for k, v in data.engines["alist"].items():
                if hasattr(s.engines.alist, k):
                    setattr(s.engines.alist, k, v)
    save_settings(s)
    from app import config as config_module

    config_module.settings = load_settings()
    return await get_settings()


@router.get("/engines", dependencies=[Depends(verify_api_key)])
async def list_engines() -> dict:
    return await get_system_summary()


@router.get("/engines/{name}", dependencies=[Depends(verify_api_key)])
async def get_engine(name: str) -> dict:
    info = await get_engine_status(name)
    if not info:
        raise HTTPException(status_code=404, detail=f"Unknown engine: {name}")
    return status_to_dict(info)


@router.post("/engines/{name}/test", dependencies=[Depends(verify_api_key)])
async def test_engine(name: str) -> dict:
    info = await get_engine_status(name)
    if not info:
        raise HTTPException(status_code=404, detail=f"Unknown engine: {name}")
    return status_to_dict(info)

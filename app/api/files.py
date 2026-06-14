from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse

from app.api.routes import verify_api_key
from app.config import load_settings
from app.services.file_manager import (
    delete_path,
    get_file_for_serve,
    get_public_base_url,
    list_directory,
    normalize_rel_path,
)
from app.services.playlist_service import playlist_service

router = APIRouter(tags=["files"])


def _public_base(request: Request) -> str:
    return get_public_base_url(str(request.base_url).rstrip("/"))


@router.get("/api/v1/files", dependencies=[Depends(verify_api_key)])
async def api_list_files(
    request: Request,
    path: str = Query(""),
) -> dict:
    try:
        data = list_directory(path, _public_base(request))
        return data.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/v1/files", dependencies=[Depends(verify_api_key)])
async def api_delete_file(path: str = Query(...)) -> dict:
    try:
        rel = normalize_rel_path(path)
        delete_path(path)
        if rel:
            await playlist_service.remove_items_by_rel_path(rel)
        return {"ok": True, "path": path}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/files/{file_path:path}")
async def serve_public_file(request: Request, file_path: str) -> FileResponse:
    s = load_settings()
    if not s.files.public_access:
        verify_api_key(request)
    try:
        target = get_file_for_serve(file_path)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return FileResponse(
        path=target,
        filename=target.name,
        media_type="application/octet-stream",
    )

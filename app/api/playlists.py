from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.routes import verify_api_key
from app.models.playlist import PlaylistCreate, PlaylistItemCreate, PlaylistItemResponse, PlaylistResponse
from app.services.file_manager import get_public_base_url
from app.services.playlist_service import playlist_service

router = APIRouter(tags=["playlists"])


def _public_base(request: Request) -> str:
    return get_public_base_url(str(request.base_url).rstrip("/"))


@router.get("/api/v1/playlists", response_model=list[PlaylistResponse])
async def list_playlists() -> list[PlaylistResponse]:
    return await playlist_service.list_playlists()


@router.get("/api/v1/playlists/default", response_model=PlaylistResponse)
async def get_default_playlist() -> PlaylistResponse:
    return await playlist_service.get_default_playlist()


@router.get(
    "/api/v1/playlists/default/items",
    response_model=list[PlaylistItemResponse],
)
async def list_default_items(request: Request) -> list[PlaylistItemResponse]:
    default = await playlist_service.get_default_playlist()
    return await playlist_service.list_items(default.id, _public_base(request))


@router.get("/api/v1/playlists/{playlist_id}", response_model=PlaylistResponse)
async def get_playlist(playlist_id: int) -> PlaylistResponse:
    playlist = await playlist_service.get_playlist(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="播放列表不存在")
    return playlist


@router.get(
    "/api/v1/playlists/{playlist_id}/items",
    response_model=list[PlaylistItemResponse],
)
async def list_playlist_items(
    request: Request, playlist_id: int
) -> list[PlaylistItemResponse]:
    try:
        return await playlist_service.list_items(playlist_id, _public_base(request))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/api/v1/media/files",
    response_model=list[PlaylistItemResponse],
)
async def list_media_files(request: Request) -> list[PlaylistItemResponse]:
    return await playlist_service.list_media_files(_public_base(request))


@router.post(
    "/api/v1/playlists",
    response_model=PlaylistResponse,
    dependencies=[Depends(verify_api_key)],
)
async def create_playlist(data: PlaylistCreate) -> PlaylistResponse:
    try:
        return await playlist_service.create_playlist(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/api/v1/playlists/{playlist_id}",
    dependencies=[Depends(verify_api_key)],
)
async def delete_playlist(playlist_id: int) -> dict:
    try:
        await playlist_service.delete_playlist(playlist_id)
        return {"ok": True, "id": playlist_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/api/v1/playlists/{playlist_id}/items",
    response_model=PlaylistItemResponse,
    dependencies=[Depends(verify_api_key)],
)
async def add_playlist_item(
    request: Request, playlist_id: int, data: PlaylistItemCreate
) -> PlaylistItemResponse:
    try:
        return await playlist_service.add_item(
            playlist_id,
            rel_path=data.rel_path,
            task_id=data.task_id,
            public_base=_public_base(request),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/api/v1/playlists/{playlist_id}/items/{item_id}",
    dependencies=[Depends(verify_api_key)],
)
async def remove_playlist_item(playlist_id: int, item_id: int) -> dict:
    try:
        await playlist_service.remove_item(playlist_id, item_id)
        return {"ok": True, "id": item_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

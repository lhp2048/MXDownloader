import io
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_NAME = "family-mediacenter"
SKILL_DIR = PROJECT_ROOT / "skills" / SKILL_NAME
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DEFAULT_BASE = "http://127.0.0.1:18026"

router = APIRouter(tags=["skills"])


def _request_base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


def _replace_base_url(content: str, base_url: str) -> str:
    return content.replace(DEFAULT_BASE, base_url)


@router.get(f"/skills/{SKILL_NAME}/SKILL.md")
async def get_skill_md(request: Request) -> Response:
    path = SKILL_DIR / "SKILL.md"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="SKILL.md not found")
    content = _replace_base_url(path.read_text(encoding="utf-8"), _request_base_url(request))
    return Response(content=content, media_type="text/markdown; charset=utf-8")


@router.get(f"/skills/{SKILL_NAME}/references/api.md")
async def get_skill_api_ref(request: Request) -> Response:
    path = SKILL_DIR / "references" / "api.md"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="api.md not found")
    content = _replace_base_url(path.read_text(encoding="utf-8"), _request_base_url(request))
    return Response(content=content, media_type="text/markdown; charset=utf-8")


@router.get(f"/skills/{SKILL_NAME}/bundle.zip")
async def get_skill_bundle(request: Request) -> Response:
    base_url = _request_base_url(request)
    skill_md = _replace_base_url(
        (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"),
        base_url,
    )
    api_md = _replace_base_url(
        (SKILL_DIR / "references" / "api.md").read_text(encoding="utf-8"),
        base_url,
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{SKILL_NAME}/SKILL.md", skill_md)
        zf.writestr(f"{SKILL_NAME}/references/api.md", api_md)
    buffer.seek(0)
    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{SKILL_NAME}-skill.zip"'},
    )


@router.get("/scripts/install-workbuddy-skill.sh")
async def get_install_script_sh() -> FileResponse:
    path = SCRIPTS_DIR / "install-workbuddy-skill.sh"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="install script not found")
    return FileResponse(path, media_type="text/x-sh", filename="install-workbuddy-skill.sh")


@router.get("/scripts/install-workbuddy-skill.ps1")
async def get_install_script_ps1() -> FileResponse:
    path = SCRIPTS_DIR / "install-workbuddy-skill.ps1"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="install script not found")
    return FileResponse(path, media_type="text/plain", filename="install-workbuddy-skill.ps1")

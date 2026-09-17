"""Minimal local API over the existing organizer."""

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from smart_organizer.organizer import organize

LOGGER = logging.getLogger(__name__)
WEB_DIR = Path(__file__).parent
DEMO_DIR = WEB_DIR.parents[1] / "demo-files"

app = FastAPI(title="Smart File Organizer", docs_url=None, redoc_url=None)


class FolderRequest(BaseModel):
    path: str = Field(min_length=1)


def chosen_folder(raw: str) -> Path:
    """Accept only an explicit absolute directory without traversal or symlink components."""
    path = Path(raw).expanduser()
    if not path.is_absolute() or ".." in path.parts or path == Path("/"):
        raise HTTPException(400, "Enter an absolute folder path without '..'.")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise HTTPException(400, "Symlink paths are not supported.")
    if not path.is_dir():
        raise HTTPException(400, "Folder does not exist or is not a directory.")
    return path.resolve()


@app.get("/")
async def index() -> HTMLResponse:
    return HTMLResponse((WEB_DIR / "templates" / "index.html").read_text(encoding="utf-8"))


@app.get("/static/{filename}")
async def static_file(filename: str) -> Response:
    media_types = {
        "styles.css": "text/css",
        "app.js": "text/javascript",
        "favicon.svg": "image/svg+xml",
    }
    if filename not in media_types:
        raise HTTPException(404, "File not found.")
    content = (WEB_DIR / "static" / filename).read_text(encoding="utf-8")
    return Response(content, media_type=media_types[filename])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/config")
async def config() -> dict[str, str | None]:
    return {"demo_path": str(DEMO_DIR) if DEMO_DIR.is_dir() else None}


@app.post("/api/preview")
async def preview(request: FolderRequest) -> dict[str, object]:
    folder = chosen_folder(request.path)
    try:
        return organize(folder, dry_run=True, quiet=True).as_dict()
    except OSError as error:
        LOGGER.exception("Preview failed for %s", folder)
        raise HTTPException(500, "Could not analyze the folder.") from error


@app.post("/api/organize")
async def execute(request: FolderRequest) -> dict[str, object]:
    folder = chosen_folder(request.path)
    try:
        return organize(folder, quiet=True).as_dict()
    except OSError as error:
        LOGGER.exception("Organization failed for %s", folder)
        raise HTTPException(500, "Could not organize the folder.") from error

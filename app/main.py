import os
import mimetypes
from typing import Generator
from fastapi import FastAPI, Request, Header, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.config import settings
from app.routers import scanner, api, m3u, admin
from app.models import MediaFile

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Corporate Local IPTV System"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
if not os.path.exists("app/static"):
    os.makedirs("app/static")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include Routers
app.include_router(scanner.router, prefix="/api", tags=["Scanner"])
app.include_router(api.router, prefix="/api", tags=["API"])
app.include_router(m3u.router, tags=["M3U"])
app.include_router(admin.router, tags=["Admin"])

# --- Streaming Logic ---

def iterfile(file_path: str, start: int, end: int, chunk_size: int = 1024 * 1024) -> Generator:
    with open(file_path, "rb") as f:
        f.seek(start)
        while (pos := f.tell()) <= end:
            read_size = min(chunk_size, end + 1 - pos)
            data = f.read(read_size)
            if not data:
                break
            yield data

@app.get("/stream/{media_id}")
def stream_video(
    media_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Streams a video file with Range support."""
    media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    file_path = media.path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")

    # MIME type detection
    content_type, _ = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = "application/octet-stream"

    if range_header:
        try:
            h = range_header.replace("bytes=", "").split("-")
            start = int(h[0]) if h[0] != "" else 0
            end = int(h[1]) if h[1] != "" else file_size - 1
        except ValueError:
            start = 0
            end = file_size - 1

        if start > end or start >= file_size:
            raise HTTPException(
                status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                detail="Requested Range Not Satisfiable",
            )

        chunk_size = 1024 * 1024

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(end - start + 1),
            "Content-Type": content_type,
        }

        return StreamingResponse(
            iterfile(file_path, start, end, chunk_size),
            status_code=206,
            headers=headers,
            media_type=content_type,
        )
    else:
        # No range header, stream whole file
        return StreamingResponse(
            iterfile(file_path, 0, file_size - 1),
            media_type=content_type
        )

@app.get("/")
def read_root():
    return {"message": "Welcome to Corporate IPTV System"}

import os
import mimetypes
from typing import Generator
from fastapi import FastAPI, Request, Header, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from app.database import engine, Base, get_db
from app.config import settings
from app.routers import scanner, api, m3u, admin
from app.models import MediaFile
from app.watcher import start_watcher
from app.services.media_service import sync_media_files
from app.database import SessionLocal
import threading
import sys
import asyncio

# Fix for Windows "ProactorEventLoop" closing error (WinError 10054)
# This is a known issue with Uvicorn/FastAPI on Windows.
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ==============================================================================
# ARCHITECTURE OVERVIEW
# ==============================================================================
# This application is built using the FastAPI framework for high-performance
# asynchronous API handling. It follows a modular structure:
#
# 1.  **Database Layer (SQLAlchemy + SQLite):**
#     - Defines data models (Channels, Categories, MediaFiles) in `app/models.py`.
#     - Manages persistent storage in `iptv.db`.
#
# 2.  **Service Layer (`app/services/`):**
#     - Encapsulates core business logic like file scanning and synchronization.
#     - Decouples logic from the API routes for better testability and reuse.
#
# 3.  **Watcher Service (`app/watcher.py`):**
#     - Monitors the filesystem for changes in the `media/` directory.
#     - Automatically triggers synchronization when files are added/moved/deleted.
#
# 4.  **API Layer (`app/routers/`):**
#     - Exposes RESTful endpoints for the frontend and external clients.
#     - `api.py`: CRUD operations for channels/categories.
#     - `m3u.py`: Generates the playlist file for IPTV players.
#     - `admin.py`: Serves the HTML frontend.
#
# 5.  **Streaming Engine:**
#     - Implemented directly in `main.py` (via `stream_video`).
#     - Supports HTTP Range requests, critical for seeking in video players.
# ==============================================================================

# Ensure database tables exist before app startup
Base.metadata.create_all(bind=engine)

def run_initial_scan():
    """Runs the initial media scan in a separate thread."""
    db = SessionLocal()
    try:
        sync_media_files(db)
    except Exception as e:
        print(f"Initial scan failed: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifecycle Manager.
    - Startup: Initializes the filesystem watcher thread AND runs an initial scan.
    - Shutdown: Gracefully stops the watcher thread to prevent resource leaks.
    """
    # STARTUP: Initialize the filesystem observer
    observer = start_watcher()

    # STARTUP: Run initial scan to sync DB with disk (in background to not block startup)
    scan_thread = threading.Thread(target=run_initial_scan)
    scan_thread.daemon = True
    scan_thread.start()

    yield
    # SHUTDOWN: Stop the observer
    if observer:
        observer.stop()
        observer.join()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Corporate Local IPTV System - High Performance Media Server",
    lifespan=lifespan
)

# CORS Configuration
# Allows requests from any origin, which is standard for local network appliances
# but should be restricted if exposed to the public internet.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
# Serves CSS, JS, and images for the admin interface.
if not os.path.exists("app/static"):
    os.makedirs("app/static")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Register API Routers
app.include_router(scanner.router, prefix="/api", tags=["Scanner"])
app.include_router(api.router, prefix="/api", tags=["API"])
app.include_router(m3u.router, tags=["M3U"])
app.include_router(admin.router, tags=["Admin"])

# ==============================================================================
# STREAMING ENGINE
# ==============================================================================

def iterfile(file_path: str, start: int, end: int, chunk_size: int = 1024 * 1024) -> Generator:
    """
    Generator that yields file chunks for streaming.
    Reads from the file pointer between `start` and `end` bytes.
    Chunk size defaults to 1MB for balance between memory usage and throughput.
    """
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
    """
    Stream video content with HTTP Range Request support (RFC 7233).

    This endpoint allows clients (VLC, Smart TVs, Web Browsers) to request specific
    byte ranges of a file, enabling seeking (scrubbing) and efficient buffering.

    Args:
        media_id: The ID of the media file in the database.
        request: The incoming HTTP request (contains headers).
        db: Database session.
    """
    # 1. Fetch media metadata from DB
    media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    file_path = media.path
    if not os.path.exists(file_path):
        # File might have been deleted manually without sync
        raise HTTPException(status_code=404, detail="File not found on disk")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")

    # MIME type detection
    content_type, _ = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = "application/octet-stream"

    # Handle Range Request
    if range_header:
        try:
            h = range_header.replace("bytes=", "").split("-")
            start = int(h[0]) if h[0] != "" else 0
            end = int(h[1]) if h[1] != "" else file_size - 1
        except ValueError:
            # Fallback for malformed headers
            start = 0
            end = file_size - 1

        # RFC 7233: If the value is greater than or equal to the current length of the
        # representation data, the byte range is interpreted as the remainder.
        if end >= file_size:
            end = file_size - 1

        # Validation
        if start > end or start >= file_size:
            raise HTTPException(
                status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                detail="Requested Range Not Satisfiable",
            )

        chunk_size = 1024 * 1024 # 1MB

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(end - start + 1),
            "Content-Type": content_type,
        }

        return StreamingResponse(
            iterfile(file_path, start, end, chunk_size),
            status_code=206, # Partial Content
            headers=headers,
            media_type=content_type,
        )
    else:
        # Standard request (stream whole file)
        return StreamingResponse(
            iterfile(file_path, 0, file_size - 1),
            media_type=content_type
        )

@app.get("/")
def read_root():
    """Health check / Welcome endpoint."""
    return {"message": "Welcome to Corporate IPTV System"}

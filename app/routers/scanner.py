import os
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, BackgroundTasks
from app.database import SessionLocal, get_db
from app.models import MediaFile
from app.config import settings
from app.services.media_service import sync_media_files

# ==============================================================================
# SCANNER ROUTER
# ==============================================================================
# This module provides API endpoints to trigger manual scans of the media directory.
# While the watcher service handles automatic updates, a manual trigger is useful
# for debugging, initial setup, or forcing a re-scan if the watcher misses an event.
# ==============================================================================

router = APIRouter()

def run_scan_task():
    """
    Background Task Wrapper.
    - Runs the synchronization logic in a separate thread/process to avoid blocking
      the main API loop.
    - Manages its own database session to ensure thread safety.
    """
    db = SessionLocal()
    try:
        sync_media_files(db)
    finally:
        db.close()

@router.post("/scan", tags=["System"])
def trigger_scan(background_tasks: BackgroundTasks):
    """
    Endpoint: Trigger Background Scan
    - Accepts a POST request to start scanning.
    - Returns immediately while the scan runs in the background.
    - Essential for UX responsiveness when dealing with large media libraries.
    """
    background_tasks.add_task(run_scan_task)
    return {"message": "Scanning started in background."}

import os
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, BackgroundTasks
from app.database import SessionLocal, get_db
from app.models import MediaFile
from app.config import settings

router = APIRouter()

def scan_directory(directory: str, extensions: set) -> list:
    """Recursively scan directory for files with given extensions."""
    found_files = []
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return []

    for root, _, files in os.walk(directory):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in extensions:
                full_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(full_path)
                    found_files.append({
                        "filename": file,
                        "path": full_path,
                        "size": size
                    })
                except OSError as e:
                    print(f"Error accessing file {full_path}: {e}")

    return found_files

def sync_media_files(db: Session):
    """Syncs the database with the filesystem."""
    print(f"Starting scan of {settings.MEDIA_DIR}...")

    # 1. Scan filesystem
    found_files_data = scan_directory(settings.MEDIA_DIR, settings.ALLOWED_EXTENSIONS)
    found_paths = {f["path"] for f in found_files_data}

    # 2. Get existing files from DB
    existing_files = db.query(MediaFile).all()
    existing_paths = {f.path: f for f in existing_files}

    added_count = 0
    removed_count = 0

    # 3. Add new files
    for file_data in found_files_data:
        if file_data["path"] not in existing_paths:
            new_file = MediaFile(
                filename=file_data["filename"],
                path=file_data["path"],
                size=file_data["size"]
            )
            db.add(new_file)
            added_count += 1

    # 4. Remove deleted files (files in DB but not on disk)
    for path, media_obj in existing_paths.items():
        if path not in found_paths:
            db.delete(media_obj)
            removed_count += 1

    db.commit()
    print(f"Scan complete. Added: {added_count}, Removed: {removed_count}")

def run_scan_task():
    """Background task wrapper that manages its own DB session."""
    db = SessionLocal()
    try:
        sync_media_files(db)
    finally:
        db.close()

@router.post("/scan", tags=["System"])
def trigger_scan(background_tasks: BackgroundTasks):
    """Triggers a background scan of the media directory."""
    background_tasks.add_task(run_scan_task)
    return {"message": "Scanning started in background."}

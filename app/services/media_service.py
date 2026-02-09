import os
import logging
from sqlalchemy.orm import Session
from app.models import MediaFile
from app.config import settings

logger = logging.getLogger(__name__)

def scan_directory(directory: str, extensions: set) -> list:
    """Recursively scan directory for files with given extensions."""
    found_files = []
    if not os.path.exists(directory):
        logger.warning(f"Directory not found: {directory}")
        return []

    # followlinks=True allows scanning symlinked directories, useful for external drives
    for root, _, files in os.walk(directory, followlinks=True):
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
                    logger.error(f"Error accessing file {full_path}: {e}")

    return found_files

def sync_media_files(db: Session):
    """Syncs the database with the filesystem."""
    logger.info(f"Starting scan of {settings.MEDIA_DIR}...")

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
    logger.info(f"Scan complete. Added: {added_count}, Removed: {removed_count}")
    return {"added": added_count, "removed": removed_count}

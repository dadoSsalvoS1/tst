import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from app.database import SessionLocal
from app.services.media_service import sync_media_files
from app.config import settings

logger = logging.getLogger(__name__)

class MediaEventHandler(FileSystemEventHandler):
    """
    Handles filesystem events (create, move, delete) in the media directory.
    When a relevant file is changed, it triggers a DB sync.
    """
    def __init__(self):
        super().__init__()
        self.last_sync_time = 0
        self.debounce_seconds = 2 # Prevent rapid-fire syncs

    def on_any_event(self, event):
        # We handle created, deleted, moved.
        if event.event_type in ('created', 'deleted', 'moved'):
            self._check_and_sync(event)

    def _check_and_sync(self, event):
        # Always sync on directory changes as they might contain files
        if event.is_directory:
            self._trigger_sync()
            return

        filename = os.path.basename(event.src_path)
        ext = os.path.splitext(filename)[1].lower()

        should_sync = ext in settings.ALLOWED_EXTENSIONS

        if not should_sync and hasattr(event, 'dest_path'):
             dest_filename = os.path.basename(event.dest_path)
             dest_ext = os.path.splitext(dest_filename)[1].lower()
             if dest_ext in settings.ALLOWED_EXTENSIONS:
                 should_sync = True

        if should_sync:
            self._trigger_sync()

    def _trigger_sync(self):
        current_time = time.time()
        if current_time - self.last_sync_time < self.debounce_seconds:
            return

        self.last_sync_time = current_time
        logger.info("File system change detected. Triggering sync...")

        # Create a new DB session for this thread
        db = SessionLocal()
        try:
            sync_media_files(db)
        except Exception as e:
            logger.error(f"Error during auto-sync: {e}")
        finally:
            db.close()

def start_watcher():
    """Starts the watchdog observer."""
    event_handler = MediaEventHandler()
    observer = Observer()

    if not os.path.exists(settings.MEDIA_DIR):
        os.makedirs(settings.MEDIA_DIR)

    observer.schedule(event_handler, settings.MEDIA_DIR, recursive=True)
    observer.start()
    return observer

# Corporate Local IPTV System

## Overview
A high-performance, locally-hosted IPTV system designed for corporate environments. It manages local video files, organizes them into channels and categories, and generates a standard M3U8 playlist compatible with Smart TVs and IPTV applications.

## Key Features
*   **Automatic Resource Management:**
    *   **Auto-Discovery:** Automatically detects new video files added to the `media/` folder.
    *   **Live Watching:** Instantaneously updates the database when files are moved, renamed, or deleted.
    *   **Folder Support:** Recursive scanning allows you to drop entire folder structures into the media library.
*   **Dynamic Channel Management:** Create channels, assign videos, and categorize content via a responsive web interface.
*   **High Performance Streaming:** Supports HTTP Range requests for smooth playback and seeking (scrubbing).
*   **Standard M3U8 Output:** Generates compliant playlists for VLC, TiviMate, and other players.
*   **Restricted Access:** Designed for secure, internal network usage.

## Requirements
*   Python 3.8+
*   `ffmpeg` (optional, for advanced features in future)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure:**
    *   Create a `.env` file (optional) to override defaults.
    *   Default media directory is `./media`. Place your video files there.

## Usage

1.  **Start the Server:**
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000
    ```
    *On startup, the system will perform an initial scan of the media library.*

2.  **Add Content:**
    *   Simply copy video files or folders into the `media/` directory.
    *   The system will automatically detect them and add them to the "Unassigned Media" list.

3.  **Access the Admin Interface:**
    *   Open your browser and navigate to `http://localhost:8000/admin`.
    *   Use the dashboard to create Categories and Channels.
    *   Assign your discovered media files to channels.

4.  **Connect your IPTV Player:**
    *   Playlist URL: `http://<YOUR_IP>:8000/playlist.m3u8`

## Architecture
*   **Backend:** FastAPI (Python) - High performance async framework.
*   **Database:** SQLite (SQLAlchemy) - Reliable, zero-config storage.
*   **Frontend:** HTML5 + TailwindCSS (Jinja2 Templates) - Lightweight and responsive.
*   **Watcher Service:** `watchdog` library for real-time filesystem monitoring.

## License
Proprietary / Internal Use Only.

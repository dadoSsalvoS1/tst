# Corporate Local IPTV System

## Overview
A high-performance, locally-hosted IPTV system designed for corporate environments. It manages local video files, organizes them into channels and categories, and generates a standard M3U8 playlist compatible with Smart TVs and IPTV applications.

## Key Features
*   **Local Resource Management:** Scans and indexes video files from a local directory.
*   **Dynamic Channel Management:** Create channels, assign videos, and categorize content via a web interface.
*   **High Performance Streaming:** Supports HTTP Range requests for smooth playback and seeking.
*   **Standard M3U8 Output:** Generates compliant playlists for VLC, TiviMate, and other players.
*   **Restricted Access:** Designed for internal network usage.

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

2.  **Access the Admin Interface:**
    *   Open your browser and navigate to `http://localhost:8000/admin`.
    *   Use the "Run Scan" button to index files in the `media` folder.
    *   Create Categories and Channels in the "Channels & Media" section.

3.  **Connect your IPTV Player:**
    *   Playlist URL: `http://<YOUR_IP>:8000/playlist.m3u8`

## Architecture
*   **Backend:** FastAPI (Python)
*   **Database:** SQLite (SQLAlchemy)
*   **Frontend:** HTML5 + TailwindCSS (Jinja2 Templates)
*   **Scanning:** Recursive file scanner with synchronization logic.

## License
Proprietary / Internal Use Only.

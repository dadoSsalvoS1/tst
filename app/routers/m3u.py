from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Channel, Category, ChannelMediaLink
from app.config import settings
from app.utils import get_local_ip

# ==============================================================================
# M3U GENERATOR
# ==============================================================================
# This module is responsible for generating the standard M3U8 playlist file.
# The M3U8 format is the standard for IPTV players (VLC, TiviMate, Smart IPTV).
#
# Key Requirements:
# 1.  Must be a valid plain text file.
# 2.  Must include #EXTINF headers with metadata (tvg-id, group-title, logo).
# 3.  Must provide a resolvable URL for the stream.
#
# Logic:
# - Queries all channels, joined with categories for grouping.
# - Constructs the #EXTINF metadata line for each channel.
# - Appends the stream URL pointing to our local streaming endpoint using the LAN IP.
# ==============================================================================

router = APIRouter()

@router.get("/playlist.m3u8", tags=["M3U"], response_class=PlainTextResponse)
def generate_playlist(request: Request, db: Session = Depends(get_db)):
    """
    Generate dynamic M3U8 playlist.
    - Ensures base URL uses the LAN IP for compatibility with external devices (Smart TVs).
    - Checks for relative logo paths and makes them absolute.
    - Only includes channels that have associated media files.
    """
    channels = db.query(Channel).join(Category).order_by(Category.name, Channel.number).all()

    lines = ["#EXTM3U"]

    # Use LAN IP instead of localhost/127.0.0.1 if possible
    local_ip = get_local_ip()
    port = settings.PORT
    scheme = request.url.scheme

    # Check if request.base_url host is localhost/127.0.0.1
    host = request.url.hostname

    if host in ["localhost", "127.0.0.1", "0.0.0.0"]:
        base_url = f"{scheme}://{local_ip}:{port}"
    else:
        # Respect the incoming request (e.g. if accessed via a reverse proxy or public domain)
        base_url = str(request.base_url).rstrip("/")

    for channel in channels:
        # Determine the primary media file for the channel.
        # Currently, the system supports linking multiple files, but for a standard
        # live stream playlist, we typically point to the first item.
        # Future enhancement: Point to a specific playlist endpoint per channel.
        first_link = db.query(ChannelMediaLink).filter(
            ChannelMediaLink.channel_id == channel.id
        ).order_by(ChannelMediaLink.order).first()

        if first_link:
            stream_url = f"{base_url}/stream/{first_link.media_file_id}"

            # Handle Logo URL
            logo = channel.logo_url if channel.logo_url else ""
            if logo and not logo.startswith("http"):
                # Normalize relative paths
                if logo.startswith("/"):
                    logo = f"{base_url}{logo}"
                else:
                    logo = f"{base_url}/{logo}"

            # Group Title (Category Name)
            category_name = channel.category.name if channel.category else "Uncategorized"

            # Construct EXTINF Line
            # Standard format: #EXTINF:-1 tvg-id="ID" tvg-name="NAME" tvg-logo="URL" group-title="GROUP",DISPLAY_NAME
            extinf = f'#EXTINF:-1 tvg-id="{channel.id}" tvg-name="{channel.name}" tvg-logo="{logo}" group-title="{category_name}",{channel.name}'

            lines.append(extinf)
            lines.append(stream_url)

    return "\n".join(lines)

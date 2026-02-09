from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Channel, Category, ChannelMediaLink

router = APIRouter()

@router.get("/playlist.m3u8", tags=["M3U"], response_class=PlainTextResponse)
def generate_playlist(request: Request, db: Session = Depends(get_db)):
    """Generates the M3U8 playlist for all channels."""
    channels = db.query(Channel).join(Category).order_by(Category.name, Channel.number).all()

    lines = ["#EXTM3U"]

    # We need the full base URL including scheme and host
    base_url = str(request.base_url).rstrip("/")

    for channel in channels:
        # Get the first media link for now
        # Ideally, we would point to a specific playlist endpoint per channel
        # But for direct playback, pointing to the stream URL is safest
        first_link = db.query(ChannelMediaLink).filter(
            ChannelMediaLink.channel_id == channel.id
        ).order_by(ChannelMediaLink.order).first()

        if first_link:
            stream_url = f"{base_url}/stream/{first_link.media_file_id}"

            logo = channel.logo_url if channel.logo_url else ""
            if logo and not logo.startswith("http"):
                # Assume relative path, prepend base_url
                if logo.startswith("/"):
                    logo = f"{base_url}{logo}"
                else:
                    logo = f"{base_url}/{logo}"

            category_name = channel.category.name if channel.category else "Uncategorized"

            # Construct the EXTINF line
            extinf = f'#EXTINF:-1 tvg-id="{channel.id}" tvg-name="{channel.name}" tvg-logo="{logo}" group-title="{category_name}",{channel.name}'

            lines.append(extinf)
            lines.append(stream_url)

    return "\n".join(lines)

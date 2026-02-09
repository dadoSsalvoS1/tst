from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Category, Channel, MediaFile, ChannelMediaLink

# ==============================================================================
# ADMIN INTERFACE
# ==============================================================================
# This router handles the web-based admin panel.
# - Uses Jinja2 templates (Server-Side Rendering) for simplicity and speed.
# - Provides CRUD forms for managing channels and categories.
# - The UI is designed to be responsive (using Tailwind CSS via CDN).
#
# Future Enhancements:
# - Add authentication (Login/Password).
# - Add drag-and-drop playlist reordering.
# ==============================================================================

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    """Admin Dashboard View."""
    media_count = db.query(MediaFile).count()
    channel_count = db.query(Channel).count()
    category_count = db.query(Category).count()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "media_count": media_count,
        "channel_count": channel_count,
        "category_count": category_count
    })

@router.get("/admin/channels", response_class=HTMLResponse)
def manage_channels(request: Request, db: Session = Depends(get_db)):
    """Channel Management View."""
    categories = db.query(Category).all()
    channels = db.query(Channel).all()
    media_files = db.query(MediaFile).all()

    return templates.TemplateResponse("channels.html", {
        "request": request,
        "categories": categories,
        "channels": channels,
        "media_files": media_files
    })

@router.post("/admin/channels/create", response_class=HTMLResponse)
def create_channel_form(
    request: Request,
    name: str = Form(...),
    category_id: int = Form(...),
    media_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Handle POST request to create a new channel.
    - Creates the Channel record.
    - Creates a ChannelMediaLink to associate the selected media file.
    """
    # Create Channel
    new_channel = Channel(name=name, category_id=category_id)
    db.add(new_channel)
    db.commit()
    db.refresh(new_channel)

    # Link Media
    link = ChannelMediaLink(channel_id=new_channel.id, media_file_id=media_id, order=0)
    db.add(link)
    db.commit()

    return RedirectResponse(url="/admin/channels", status_code=303)

@router.post("/admin/categories/create", response_class=HTMLResponse)
def create_category_form(
    request: Request,
    name: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Handle POST request to create a new category.
    - Generates a slug automatically.
    - Prevents duplicates (though the DB constraint handles this too).
    """
    # Check if exists
    if not db.query(Category).filter(Category.name == name).first():
        new_cat = Category(name=name, slug=name.lower().replace(" ", "-"))
        db.add(new_cat)
        db.commit()

    return RedirectResponse(url="/admin/channels", status_code=303)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.database import get_db
from app.models import Category, Channel, MediaFile, ChannelMediaLink

router = APIRouter()

# --- Pydantic Schemas ---
class CategoryBase(BaseModel):
    name: str
    slug: str
    icon_url: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryOut(CategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ChannelBase(BaseModel):
    name: str
    number: Optional[int] = None
    logo_url: Optional[str] = None
    category_id: int

class ChannelCreate(ChannelBase):
    media_file_ids: List[int] = []

class MediaFileOut(BaseModel):
    id: int
    filename: str
    path: str
    size: int
    model_config = ConfigDict(from_attributes=True)

class ChannelMediaLinkOut(BaseModel):
    media_file: MediaFileOut
    order: int
    model_config = ConfigDict(from_attributes=True)

class ChannelOut(ChannelBase):
    id: int
    media_links: List[ChannelMediaLinkOut] = []
    model_config = ConfigDict(from_attributes=True)

# --- Endpoints ---

@router.get("/media", response_model=List[MediaFileOut])
def list_media(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all available media files."""
    return db.query(MediaFile).offset(skip).limit(limit).all()

@router.post("/categories", response_model=CategoryOut)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new category."""
    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/categories", response_model=List[CategoryOut])
def list_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all categories."""
    return db.query(Category).offset(skip).limit(limit).all()

@router.post("/channels", response_model=ChannelOut)
def create_channel(channel: ChannelCreate, db: Session = Depends(get_db)):
    """Create a new channel and link media files."""
    # check category exists
    cat = db.query(Category).filter(Category.id == channel.category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    channel_data = channel.model_dump(exclude={"media_file_ids"})
    db_channel = Channel(**channel_data)
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)

    # Link media files
    for idx, media_id in enumerate(channel.media_file_ids):
        # Verify media file exists
        media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
        if media:
            link = ChannelMediaLink(
                channel_id=db_channel.id,
                media_file_id=media_id,
                order=idx
            )
            db.add(link)

    db.commit()
    db.refresh(db_channel) # Refresh to load relationships
    return db_channel

@router.get("/channels", response_model=List[ChannelOut])
def list_channels(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all channels."""
    channels = db.query(Channel).offset(skip).limit(limit).all()
    return channels

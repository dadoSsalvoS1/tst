from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

# ==============================================================================
# DATA MODELS (ORM)
# ==============================================================================
# The system uses SQLAlchemy ORM to map Python classes to SQLite tables.
# The schema is designed for flexibility, allowing multiple media files to be
# associated with a single channel (playlist style) and organized into
# categories.
#
# Relationships:
# - Category (1) -> (Many) Channel
# - Channel (1) -> (Many) ChannelMediaLink (Order) -> (1) MediaFile
# - MediaFile (1) -> (Many) ChannelMediaLink
# ==============================================================================

class MediaFile(Base):
    """
    Represents a physical video file on the disk.
    - Stores metadata like size, duration (future), and path.
    - Path must be unique to prevent duplicate entries for the same file.
    - `filename` is indexed for faster searching.
    """
    __tablename__ = "media_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    path = Column(String, unique=True, index=True)
    size = Column(Integer)
    duration = Column(Integer, nullable=True)  # Duration in seconds (placeholder for ffmpeg integration)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship: A file can belong to many channels via the link table
    channel_links = relationship("ChannelMediaLink", back_populates="media_file")

    def __repr__(self):
        return f"<MediaFile(filename={self.filename})>"


class Category(Base):
    """
    Represents a grouping of channels (e.g., Movies, Sports, News).
    - `slug` is used for potential URL-friendly routing in the future.
    - `icon_url` allows categories to have visual representation in UI.
    """
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    slug = Column(String, unique=True, index=True)
    icon_url = Column(String, nullable=True)

    # Relationship: Deleting a category deletes all its channels (cascade)
    channels = relationship("Channel", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category(name={self.name})>"


class Channel(Base):
    """
    Represents an IPTV channel.
    - Has a `number` field for traditional TV listing ordering (Channel 1, 2, etc.).
    - Linked to a single Category.
    - Can contain multiple media files (via `media_links`) to form a playlist.
    """
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    number = Column(Integer, index=True, nullable=True)
    logo_url = Column(String, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"))

    # Relationship to Category
    category = relationship("Category", back_populates="channels")

    # Relationship to MediaFiles (via Link table)
    # Deleting a channel removes the links, but NOT the media files themselves.
    media_links = relationship("ChannelMediaLink", back_populates="channel", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Channel(name={self.name})>"


class ChannelMediaLink(Base):
    """
    Association table between Channels and MediaFiles.
    - Allows a Many-to-Many relationship with additional metadata (`order`).
    - `order` determines the sequence of playback for multi-file channels.
    """
    __tablename__ = "channel_media_links"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"))
    media_file_id = Column(Integer, ForeignKey("media_files.id"))
    order = Column(Integer, default=0)

    channel = relationship("Channel", back_populates="media_links")
    media_file = relationship("MediaFile", back_populates="channel_links")

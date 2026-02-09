from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class MediaFile(Base):
    """Represents a physical video file on the disk."""
    __tablename__ = "media_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    path = Column(String, unique=True, index=True)
    size = Column(Integer)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to ChannelMediaLink
    channel_links = relationship("ChannelMediaLink", back_populates="media_file")

    def __repr__(self):
        return f"<MediaFile(filename={self.filename})>"


class Category(Base):
    """Represents a category of channels (e.g., Movies, Sports)."""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    slug = Column(String, unique=True, index=True)
    icon_url = Column(String, nullable=True)

    # Relationship to Channels
    channels = relationship("Channel", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category(name={self.name})>"


class Channel(Base):
    """Represents an IPTV channel."""
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    number = Column(Integer, index=True, nullable=True)
    logo_url = Column(String, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"))

    # Relationship to Category
    category = relationship("Category", back_populates="channels")

    # Relationship to MediaFiles (via Link table)
    media_links = relationship("ChannelMediaLink", back_populates="channel", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Channel(name={self.name})>"


class ChannelMediaLink(Base):
    """Link table to associate MediaFiles with Channels (Many-to-Many with order)."""
    __tablename__ = "channel_media_links"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"))
    media_file_id = Column(Integer, ForeignKey("media_files.id"))
    order = Column(Integer, default=0)

    channel = relationship("Channel", back_populates="media_links")
    media_file = relationship("MediaFile", back_populates="channel_links")

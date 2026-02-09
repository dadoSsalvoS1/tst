import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import MediaFile, Category, Channel, ChannelMediaLink

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# --- Basic Tests ---

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Corporate IPTV System"}

def test_create_category():
    response = client.post(
        "/api/categories",
        json={"name": "Test Category", "slug": "test-category"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Category"
    assert "id" in data

def test_playlist_empty():
    response = client.get("/playlist.m3u8")
    assert response.status_code == 200
    assert response.text.startswith("#EXTM3U")

# --- Admin Channel Management Tests ---

def setup_data():
    db = TestingSessionLocal()
    uid = str(uuid.uuid4())
    m1 = MediaFile(filename=f"vid1_{uid}.mp4", path=f"/tmp/vid1_{uid}.mp4", size=100)
    m2 = MediaFile(filename=f"vid2_{uid}.mp4", path=f"/tmp/vid2_{uid}.mp4", size=200)

    # Check if exists (shouldn't with uuid but just in case)
    if not db.query(MediaFile).filter(MediaFile.path == m1.path).first():
        db.add(m1)
    if not db.query(MediaFile).filter(MediaFile.path == m2.path).first():
        db.add(m2)

    cat = Category(name=f"TestCat_{uid}", slug=f"testcat_{uid}")
    db.add(cat)

    db.commit()
    db.refresh(m1)
    db.refresh(m2)
    db.refresh(cat)

    return cat.id, m1.id, m2.id

def test_create_channel_multiple_media():
    cat_id, m1_id, m2_id = setup_data()
    unique_name = f"MultiMediaChannel_{uuid.uuid4()}"

    # Simulate form submission
    # Note: Using data directly with list for same key
    response = client.post(
        "/admin/channels/create",
        data={
            "name": unique_name,
            "category_id": cat_id,
            "media_ids": [m1_id, m2_id]
        },
        follow_redirects=False
    )

    assert response.status_code == 303

    # Verify in DB
    db = TestingSessionLocal()
    channel = db.query(Channel).filter(Channel.name == unique_name).first()
    assert channel is not None
    assert len(channel.media_links) == 2

    media_ids_linked = {link.media_file_id for link in channel.media_links}
    assert m1_id in media_ids_linked
    assert m2_id in media_ids_linked

def test_create_channel_no_media():
    cat_id, _, _ = setup_data()
    unique_name = f"NoMediaChannel_{uuid.uuid4()}"

    response = client.post(
        "/admin/channels/create",
        data={
            "name": unique_name,
            "category_id": cat_id
            # No media_ids sent
        },
        follow_redirects=False
    )

    assert response.status_code == 303

    db = TestingSessionLocal()
    channel = db.query(Channel).filter(Channel.name == unique_name).first()
    assert channel is not None
    assert len(channel.media_links) == 0

def test_delete_channel():
    db = TestingSessionLocal()
    uid = str(uuid.uuid4())
    cat = Category(name=f"DelCat_{uid}", slug=f"del_{uid}")
    db.add(cat)
    db.commit()
    db.refresh(cat)

    c = Channel(name=f"ToDelete_{uid}", category_id=cat.id)
    db.add(c)
    db.commit()
    c_id = c.id

    response = client.post(f"/admin/channels/delete/{c_id}", follow_redirects=False)
    assert response.status_code == 303

    assert db.query(Channel).filter(Channel.id == c_id).first() is None

def test_delete_category():
    db = TestingSessionLocal()
    uid = str(uuid.uuid4())
    cat = Category(name=f"CatToDelete_{uid}", slug=f"delcat_{uid}")
    db.add(cat)
    db.commit()
    cat_id = cat.id

    # Add a channel to verify cascade (if SQLAlchemy handles it) or manual deletion logic
    # In models.py: channels = relationship("Channel", back_populates="category", cascade="all, delete-orphan")
    c = Channel(name=f"CascadedDelete_{uid}", category_id=cat.id)
    db.add(c)
    db.commit()
    c_id = c.id

    response = client.post(f"/admin/categories/delete/{cat_id}", follow_redirects=False)
    assert response.status_code == 303

    assert db.query(Category).filter(Category.id == cat_id).first() is None
    # Verify cascade
    assert db.query(Channel).filter(Channel.id == c_id).first() is None

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================
# The system uses SQLite for portability and ease of setup.
# In a high-concurrency corporate environment, this could be swapped for
# PostgreSQL by changing the `DATABASE_URL` in `app/config.py` and installing
# `psycopg2`.
#
# Thread Safety:
# - SQLite is single-writer.
# - check_same_thread=False allows multiple threads to access the connection,
#   which is necessary for FastAPI's async nature + background tasks.
# ==============================================================================

# Create the SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a SessionLocal class for database sessions
# autocommit=False: Ensures we manually commit transactions (safety).
# autoflush=False: Ensures we manually flush changes (performance).
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """
    Dependency for getting a database session.
    - Yields a session for the request scope.
    - Ensures the session is closed after the request is processed.
    - Used via `Depends(get_db)` in FastAPI routes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

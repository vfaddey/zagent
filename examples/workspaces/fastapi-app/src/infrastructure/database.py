# infrastructure/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Using an in-memory database for isolation in tests, but allowing connection strings.
# For default usage/test setup, we might prefer ':memory:'.
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_book_db.sqlite"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency to provide a thread-safe database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

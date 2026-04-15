# tests/test_books.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, Integer, String, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base

# --- Setup for testing: Use an in-memory SQLite database ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# FIX: Initialize declarative base correctly
Base = declarative_base()


# 1. Define the Test Model using the newly fixed imports
class TestBookModel(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    year = Column(Integer)

# 2. Automatically create the necessary tables in the in-memory database
# Use MetaData to ensure we create the table using the defined Base.
Base.metadata.create_all(engine)


# --- Fixture for Test Client Setup ---

@pytest.fixture(scope="function") # Changed scope to 'function' for full isolation between tests
def db_session():
    """Provides a fresh, transactional session for each test function."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function") # Changed scope to 'function'
def client(db_session):
    """Provides the TestClient instance configured with the current DB session."""
    from src.presentation import api
    from src.application.use_cases import BookService
    from src.infrastructure.repositories_impl import SQLAlchemyBookRepository
    from src.infrastructure.database import get_db

    # 1. Dependency Overriding: Re-implementing the dependency injection layer for the test client
    def override_get_db():
        yield db_session

    # Manually override the dependency on the FastAPI app instance
    app = api.app # API needs to expose 'app' or we mock it. We assume the router setup makes 'app' available.
    app.dependency_overrides[get_db] = override_get_db
    
    client_instance = TestClient(app)
    
    yield client_instance
    
    # Cleanup overrides after test run
    app.dependency_overrides.clear()


# --- Test Cases ---
def test_health_endpoint(client):
    """Tests the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "BookTrackerAPI", "version": "1.0.0"}

def test_create_book_success(client, db_session):
    """Tests successful creation of a book."""
    book_data = {"title": "The Martian", "author": "Andy Weir", "year": 2011}
    response = client.post("/books/", json=book_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data['title'] == "The Martian"
    assert isinstance(data['id'], int)
    
    # Transaction boundary: The session fixture handles commit/rollback.

def test_get_all_books_success(client, db_session):
    """Tests retrieving all books."""
    # Setup: Create two books first
    client.post("/books/", json={"title": "Dune", "author": "Frank Herbert", "year": 1965})
    client.post("/books/", json={"title": "1984", "author": "George Orwell", "year": 1949})
    
    response = client.get("/books/")
    assert response.status_code == 200
    data = response.json()
    assert len(data['books']) == 2
    
def test_get_book_by_id_success(client, db_session):
    """Tests retrieving a specific book by ID."""
    # Setup: Create a book we will retrieve
    book_data = {"title": "Foundation", "author": "Isaac Asimov", "year": 1951}
    response_create = client.post("/books/", json=book_data)
    book_id = response_create.json()['id']
    
    # Test retrieval
    response = client.get(f"/books/{book_id}")
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == book_id
    assert data['title'] == "Foundation"

def test_get_book_not_found(client):
    """Tests 404 handling for non-existent book ID."""
    # Attempt to get book 999
    response = client.get("/books/999")
    assert response.status_code == 404
    assert response.json()['detail'] == "Book not found"

def test_create_book_validation_error(client):
    """Tests validation errors (e.g., missing title)."""
    # Missing required field 'title'
    invalid_data = {"author": "Anon", "year": 2000}
    response = client.post("/books/", json=invalid_data)
    assert response.status_code == 400
    assert "Title and author cannot be empty." in response.json()['detail']

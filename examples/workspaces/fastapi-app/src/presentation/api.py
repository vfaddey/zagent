# presentation/api.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.domain.repositories import BookRepository  # FIX: Fully qualified import
from application.use_cases import BookService         # FIX: Fully qualified import
from infrastructure.repositories_impl import SQLAlchemyBookRepository
from infrastructure.database import get_db
from presentation.models import BookCreate, BookResponse, BookListResponse, NotFoundError

router = APIRouter(prefix="/books", tags=["Books"])

# Dependency to inject UseCase, which in turn requires the Repository implementation
def get_book_service(db: Session = Depends(get_db)) -> BookService:
    """Factory function to create service instance bound to the current DB session."""
    # Dependency injection chain: DB -> Repository Impl -> Service UseCase
    repo = SQLAlchemyBookRepository(db=db)
    return BookService(repository=repo)

@router.get("/", response_model=BookListResponse)
def list_books_endpoint(
    service: BookService = Depends(get_book_service)
):
    """Endpoint to list all books."""
    books_domain = service.get_all_books()
    # Mapping domain entities to Pydantic model structure for response
    # We need to ensure BookResponse can correctly capture all fields from the domain entity when validating
    book_responses = [BookResponse.model_validate(book).__dict__ for book in books_domain]
    return BookListResponse(books=book_responses)

@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book_endpoint(
    book_in: BookCreate,
    service: BookService = Depends(get_book_service)
):
    """Endpoint to create a new book."""
    try:
        # 1. Execute business logic (Use Case)
        book_domain = service.create_book(
            title=book_in.title,
            author=book_in.author,
            year=book_in.year
        )
        # 2. Convert domain entity to response model
        return BookResponse.model_validate(book_domain)
    except ValueError as e:
        # Handles validation errors from the Use Case layer
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{book_id}", response_model=BookResponse)
def get_book_endpoint(
    book_id: int,
    service: BookService = Depends(get_book_service)
):
    """Endpoint to retrieve a book by ID."""
    book_domain = service.get_book(book_id)
    if book_domain is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    return BookResponse.model_validate(book_domain)

# -------------------------------------------------
# Health Check Endpoint (Requirement)
# ------------------------------
@router.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "BookTrackerAPI", "version": "1.0.0"}

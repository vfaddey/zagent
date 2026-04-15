# presentation/models.py
from pydantic import BaseModel
from typing import List

# Request Body Schema
class BookCreate(BaseModel):
    title: str
    author: str
    year: int

# Response Schema
class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    year: int

    class Config:
        from_attributes = True

# List Response Schema (can reuse BookResponse or use a dedicated one)
class BookListResponse(BaseModel):
    books: List[BookResponse]

# Custom Exception Handling for clarity
class NotFoundError(Exception):
    """Custom exception raised when a resource is not found."""
    pass

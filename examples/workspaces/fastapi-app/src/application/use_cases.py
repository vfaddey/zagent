# application/use_cases.py
from typing import List, Optional
from domain.entities import Book
from domain.repositories import BookRepository

class BookService:
    """
    Application/Use Case Layer. Contains core business logic.
    Depends only on the repository interface, not the implementation.
    """
    def __init__(self, repository: BookRepository):
        self._repository = repository

    def create_book(self, title: str, author: str, year: int) -> Book:
        """Handles creation logic."""
        if not title or not author:
            # In a real app, we'd raise a specific DomainException
            raise ValueError("Title and author cannot be empty.")
        
        new_book = Book(id=None, title=title, author=author, year=year)
        return self._repository.add(new_book)

    def get_book(self, book_id: int) -> Optional[Book]:
        """Fetches a book by ID."""
        return self._repository.get_by_id(book_id)

    def get_all_books(self) -> List[Book]:
        """Fetches all books."""
        return self._repository.get_all()

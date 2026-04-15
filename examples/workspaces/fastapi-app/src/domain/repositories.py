# domain/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import Book

class BookRepository(ABC):
    """
    Repository Interface defining book persistence operations.
    This interface ensures business logic is decoupled from database specifics.
    """
    @abstractmethod
    def get_by_id(self, book_id: int) -> Optional[Book]:
        pass

    @abstractmethod
    def get_all(self) -> List[Book]:
        pass

    @abstractmethod
    def add(self, book: Book) -> Book:
        """Adds a new book and returns the book with its assigned ID."""
        pass

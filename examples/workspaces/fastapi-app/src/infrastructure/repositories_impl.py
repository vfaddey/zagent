# infrastructure/repositories_impl.py
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Year
from typing import List, Optional
from domain.entities import Book
from domain.repositories import BookRepository
from .database import Base # Uses Base defined in infrastructure/database.py

# 1. SQLAlchemy Model (Persistence Detail)
class BookModel(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    year = Column(Integer)

# 2. Repository Implementation
class SQLAlchemyBookRepository(BookRepository):
    def __init__(self, db: Session):
        """Requires a DB session to operate."""
        self.db = db

    def get_by_id(self, book_id: int) -> Optional[Book]:
        model = self.db.query(BookModel).filter(BookModel.id == book_id).first()
        if model:
            return Book(id=model.id, title=model.title, author=model.author, year=model.year)
        return None

    def get_all(self) -> List[Book]:
        models = self.db.query(BookModel).all()
        return [Book(id=m.id, title=m.title, author=m.author, year=m.year) for m in models]

    def add(self, book: Book) -> Book:
        # Create model instance from domain entity
        db_book = BookModel(
            title=book.title,
            author=book.author,
            year=book.year
        )
        
        # Database operation (writes state)
        self.db.add(db_book)
        self.db.commit()
        self.db.refresh(db_book)
        
        # Return the updated domain entity with the generated ID
        return Book(id=db_book.id, title=book.title, author=book.author, year=book.year)

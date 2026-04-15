# domain/entities.py
from dataclasses import dataclass

@dataclass
class Book:
    """Domain Entity"""
    id: int | None = None
    title: str
    author: str
    year: int

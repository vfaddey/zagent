Вот структура и полный код проекта FastAPI с асинхронным SQLite.

### Структура проекта
```text
.
├── app/
│   ├── __init__.py
│   ├── db.py          # Настройка подключения к БД
│   ├── models.py      # SQLAlchemy модели
│   ├── schemas.py     # Pydantic схемы
│   ├── crud.py        # Логика работы с БД
│   ├── main.py        # Точка входа и жизненный цикл
│   └── routers/
│       ├── __init__.py
│       └── items.py   # Эндпоинты для Item
├── requirements.txt   # Зависимости
└── app.db            # Файл БД (появится после запуска)
```

---

### Код каждого файла

#### `requirements.txt`
```text
fastapi
uvicorn
sqlalchemy>=2.0.0
aiosqlite
pydantic>=2.0.0
```

#### `app/db.py`
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "sqlite+aiosqlite:///./app.db"

engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

# Dependency injection
async def get_db():
    async with SessionLocal() as session:
        yield session
```

#### `app/models.py`
```python
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[str | None] = mapped_column(default=None)
```

#### `app/schemas.py`
```python
from pydantic import BaseModel, ConfigDict

class ItemBase(BaseModel):
    name: str
    description: str | None = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(ItemBase):
    name: str | None = None

class Item(ItemBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
```

#### `app/crud.py`
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from . import models, schemas

async def get_items(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.Item).offset(skip).limit(limit))
    return result.scalars().all()

async def get_item(db: AsyncSession, item_id: int):
    result = await db.execute(select(models.Item).where(models.Item.id == item_id))
    return result.scalar_one_or_none()

async def create_item(db: AsyncSession, item: schemas.ItemCreate):
    db_item = models.Item(**item.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

async def update_item(db: AsyncSession, db_item: models.Item, item_update: schemas.ItemUpdate):
    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    await db.commit()
    await db.refresh(db_item)
    return db_item

async def delete_item(db: AsyncSession, db_item: models.Item):
    await db.delete(db_item)
    await db.commit()
```

#### `app/routers/items.py`
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .. import crud, schemas, db

router = APIRouter(prefix="/items", tags=["items"])

@router.post("/", response_model=schemas.Item, status_code=status.HTTP_201_CREATED)
async def create_item(item: schemas.ItemCreate, session: AsyncSession = Depends(db.get_db)):
    return await crud.create_item(session, item)

@router.get("/", response_model=List[schemas.Item])
async def read_items(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(db.get_db)):
    return await crud.get_items(session, skip=skip, limit=limit)

@router.get("/{item_id}", response_model=schemas.Item)
async def read_item(item_id: int, session: AsyncSession = Depends(db.get_db)):
    db_item = await crud.get_item(session, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@router.put("/{item_id}", response_model=schemas.Item)
async def update_item(item_id: int, item: schemas.ItemUpdate, session: AsyncSession = Depends(db.get_db)):
    db_item = await crud.get_item(session, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return await crud.update_item(session, db_item, item)

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int, session: AsyncSession = Depends(db.get_db)):
    db_item = await crud.get_item(session, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    await crud.delete_item(session, db_item)
```

#### `app/main.py`
```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .db import engine, Base
from .routers import items

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Автоматическое создание таблиц при старте
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title="FastAPI SQLite Async CRUD", lifespan=lifespan)

app.include_router(items.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI Item CRUD API"}
```

---

### Инструкции по запуску

1. **Установка зависимостей:**
```bash
pip install -r requirements.txt
```

2. **Запуск сервера:**
```bash
uvicorn app.main:app --reload
```

---

### Примеры cURL запросов

**Создать Item:**
```bash
curl -X POST "http://127.0.0.1:8000/items/" -H "Content-Type: application/json" -d '{"name": "Мой товар", "description": "Описание товара"}'
```

**Получить список всех Items:**
```bash
curl -X GET "http://127.0.0.1:8000/items/"
```

**Обновить Item:**
```bash
curl -X PUT "http://127.0.0.1:8000/items/1" -H "Content-Type: application/json" -d '{"name": "Новое имя"}'
```

**Удалить Item:**
```bash
curl -X DELETE "http://127.0.0.1:8000/items/1"
```

ZAGENT_DONE
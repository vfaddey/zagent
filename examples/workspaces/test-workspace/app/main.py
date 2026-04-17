from fastapi import FastAPI
from contextlib import asynccontextmanager
from .db import engine, Base
from .routers import items

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создание таблиц при старте
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Закрытие соединений при выключении (опционально)
    await engine.dispose()

app = FastAPI(title="FastAPI SQLite Async CRUD", lifespan=lifespan)

app.include_router(items.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI Item CRUD API"}

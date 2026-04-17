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

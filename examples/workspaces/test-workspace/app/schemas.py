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

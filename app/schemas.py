from typing import Literal

from pydantic import BaseModel, Field


Status = Literal['pending', 'preparing', 'out_for_delivery', 'delivered', 'cancelled']


class OrderItemInput(BaseModel):
    menu_item_id: int = Field(gt=0, strict=True)
    quantity: int = Field(gt=0, strict=True)


class OrderInput(BaseModel):
    restaurant_id: int = Field(gt=0, strict=True)
    address: str = Field(min_length=1, max_length=500)
    items: list[OrderItemInput] = Field(min_length=1)


class StatusInput(BaseModel):
    status: Status

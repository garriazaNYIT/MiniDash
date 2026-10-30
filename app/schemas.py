from pydantic import BaseModel, Field

from .order_tracking import OrderStatus

Status = OrderStatus


class OrderItemInput(BaseModel):
    menu_item_id: int = Field(gt=0, strict=True)
    quantity: int = Field(gt=0, strict=True)


class OrderInput(BaseModel):
    delivery_distance_km: float = Field(ge=0, allow_inf_nan=False, strict=True)
    restaurant_id: int = Field(gt=0, strict=True)
    address: str = Field(min_length=1, max_length=500)
    items: list[OrderItemInput] = Field(min_length=1)


class StatusInput(BaseModel):
    status: Status

# Import BaseModel, Field from pydantic.
from pydantic import BaseModel, Field

# Import OrderStatus from .order_tracking.
from .order_tracking import OrderStatus

# Set Status to OrderStatus.
Status = OrderStatus


# Define the OrderItemInput class using BaseModel.
class OrderItemInput(BaseModel):

    # Set menu_item_id to Field(gt=0, strict=True).
    menu_item_id: int = Field(gt=0, strict=True)

    # Set quantity to Field(gt=0, strict=True).
    quantity: int = Field(gt=0, strict=True)


# Define the OrderInput class using BaseModel.
class OrderInput(BaseModel):

    # Set delivery_distance_km to Field(ge=0, allow_inf_nan=False, strict=True).
    delivery_distance_km: float = Field(ge=0, allow_inf_nan=False, strict=True)

    # Set restaurant_id to Field(gt=0, strict=True).
    restaurant_id: int = Field(gt=0, strict=True)

    # Set address to Field(min_length=1, max_length=500).
    address: str = Field(min_length=1, max_length=500)

    # Set items to Field(min_length=1).
    items: list[OrderItemInput] = Field(min_length=1)


# Define the StatusInput class using BaseModel.
class StatusInput(BaseModel):

    # Declare status with type Status.
    status: Status

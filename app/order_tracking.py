"""Track C lifecycle policy, independent of HTTP and persistence."""
from enum import Enum


class OrderStatus(str, Enum):
    PLACED = 'PLACED'
    PREPARING = 'PREPARING'
    READY = 'READY'
    PICKED_UP = 'PICKED_UP'
    DELIVERED = 'DELIVERED'
    CANCELLED = 'CANCELLED'


_ALLOWED_CHANGES = frozenset({
    (OrderStatus.PLACED, OrderStatus.PREPARING),
    (OrderStatus.PLACED, OrderStatus.CANCELLED),
    (OrderStatus.PREPARING, OrderStatus.READY),
    (OrderStatus.READY, OrderStatus.PICKED_UP),
    (OrderStatus.PICKED_UP, OrderStatus.DELIVERED),
})


def is_status_change(current: str, requested: str) -> bool:
    """Return whether a valid request changes status; reject invalid requests.

    A False result is a successful no-op: callers must preserve history and ETA.
    Validation happens before equality, including for repeated unknown values.
    """
    current_status = OrderStatus(current)
    requested_status = OrderStatus(requested)
    if current_status == requested_status:
        return False
    if (current_status, requested_status) not in _ALLOWED_CHANGES:
        raise ValueError(f'Invalid status transition: {current} -> {requested}')
    return True

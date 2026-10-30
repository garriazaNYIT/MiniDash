"""Track C lifecycle policy, independent of HTTP and persistence."""

# Import Enum from enum.
from enum import Enum


# Define the OrderStatus class using str, Enum.
class OrderStatus(str, Enum):

    # Set PLACED to 'PLACED'.
    PLACED = 'PLACED'

    # Set PREPARING to 'PREPARING'.
    PREPARING = 'PREPARING'

    # Set READY to 'READY'.
    READY = 'READY'

    # Set PICKED_UP to 'PICKED_UP'.
    PICKED_UP = 'PICKED_UP'

    # Set DELIVERED to 'DELIVERED'.
    DELIVERED = 'DELIVERED'

    # Set CANCELLED to 'CANCELLED'.
    CANCELLED = 'CANCELLED'


# Build the value below and store it in _ALLOWED_CHANGES.
_ALLOWED_CHANGES = frozenset({

    # Supply the remaining arguments or values for the expression above.
    (OrderStatus.PLACED, OrderStatus.PREPARING),

    # Supply the remaining arguments or values for the expression above.
    (OrderStatus.PLACED, OrderStatus.CANCELLED),

    # Supply the remaining arguments or values for the expression above.
    (OrderStatus.PREPARING, OrderStatus.READY),

    # Supply the remaining arguments or values for the expression above.
    (OrderStatus.READY, OrderStatus.PICKED_UP),

    # Supply the remaining arguments or values for the expression above.
    (OrderStatus.PICKED_UP, OrderStatus.DELIVERED),

# Finish the expression started above.
})


# Define is status change.
def is_status_change(current: str, requested: str) -> bool:
    """Return whether a valid request changes status; reject invalid requests.

    A False result is a successful no-op: callers must preserve history and ETA.
    Validation happens before equality, including for repeated unknown values.
    """

    # Set current_status to OrderStatus(current).
    current_status = OrderStatus(current)

    # Set requested_status to OrderStatus(requested).
    requested_status = OrderStatus(requested)

    # Run this branch when current_status == requested_status.
    if current_status == requested_status:

        # Return False.
        return False

    # Run this branch when (current_status, requested_status) not in _ALLOWED_CHANGES.
    if (current_status, requested_status) not in _ALLOWED_CHANGES:

        # Raise ValueError(f'Invalid status transition: {current} -> {requested}')
        # to report the failure.
        raise ValueError(f'Invalid status transition: {current} -> {requested}')

    # Return True.
    return True

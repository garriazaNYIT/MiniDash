"""Deterministic preparation and distance estimates, using UTC datetimes."""

# Import datetime, timedelta from datetime.
from datetime import datetime, timedelta

# Import ceil from math.
from math import ceil


# Define estimate delivery.
def estimate_delivery(status, created_at, prep_minutes, distance_km, now):

    # Run this branch when status == 'CANCELLED'.
    if status == 'CANCELLED':

        # Return None.
        return None

    # Run this branch when status == 'DELIVERED'.
    if status == 'DELIVERED':

        # Return now.isoformat().
        return now.isoformat()

    # Set preparation to 0.
    preparation = 0

    # Run this branch when status in ('PLACED', 'PREPARING').
    if status in ('PLACED', 'PREPARING'):

        # Set elapsed to max(0, (now -
        # datetime.fromisoformat(created_at)).total_seconds() / 60).
        elapsed = max(0, (now - datetime.fromisoformat(created_at)).total_seconds() / 60)

        # Set preparation to max(0, prep_minutes - elapsed).
        preparation = max(0, prep_minutes - elapsed)

    # 60 minutes / 30 km per hour
    travel = ceil(distance_km * 2)

    # Return (now + timedelta(minutes=preparation + travel)).isoformat().
    return (now + timedelta(minutes=preparation + travel)).isoformat()


# Define remaining minutes.
def remaining_minutes(estimated_delivery_at, now):

    # Run this branch when estimated_delivery_at is None.
    if estimated_delivery_at is None:

        # Return None.
        return None

    # Set seconds to (datetime.fromisoformat(estimated_delivery_at) -
    # now).total_seconds().
    seconds = (datetime.fromisoformat(estimated_delivery_at) - now).total_seconds()

    # Return max(0, ceil(seconds / 60)).
    return max(0, ceil(seconds / 60))

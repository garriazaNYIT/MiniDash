"""Deterministic preparation and distance estimates, using UTC datetimes."""
from datetime import datetime, timedelta
from math import ceil


def estimate_delivery(status, created_at, prep_minutes, distance_km, now):
    if status == 'CANCELLED':
        return None
    if status == 'DELIVERED':
        return now.isoformat()
    preparation = 0
    if status in ('PLACED', 'PREPARING'):
        elapsed = max(0, (now - datetime.fromisoformat(created_at)).total_seconds() / 60)
        preparation = max(0, prep_minutes - elapsed)
    travel = ceil(distance_km * 2)  # 60 minutes / 30 km per hour
    return (now + timedelta(minutes=preparation + travel)).isoformat()


def remaining_minutes(estimated_delivery_at, now):
    if estimated_delivery_at is None:
        return None
    seconds = (datetime.fromisoformat(estimated_delivery_at) - now).total_seconds()
    return max(0, ceil(seconds / 60))

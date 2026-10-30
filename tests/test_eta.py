from datetime import datetime, timedelta, timezone

import pytest

from app.eta import estimate_delivery, remaining_minutes


START = datetime(2026, 10, 30, 12, tzinfo=timezone.utc)


@pytest.mark.parametrize('distance,travel', [(0, 0), (6, 12), (0.01, 1), (0.5, 1), (0.51, 2)])
def test_initial_preparation_and_rounded_travel(distance, travel):
    assert estimate_delivery('PLACED', START.isoformat(), 20, distance, START) == (
        START + timedelta(minutes=20 + travel)).isoformat()


@pytest.mark.parametrize('elapsed,remaining', [(5, 15), (25, 0)])
def test_preparing_subtracts_elapsed_time(elapsed, remaining):
    now = START + timedelta(minutes=elapsed)
    assert estimate_delivery('PREPARING', START.isoformat(), 20, 6, now) == (
        now + timedelta(minutes=remaining + 12)).isoformat()


@pytest.mark.parametrize('status', ['READY', 'PICKED_UP'])
def test_delivery_phases_exclude_preparation(status):
    assert estimate_delivery(status, START.isoformat(), 20, 6, START) == (
        START + timedelta(minutes=12)).isoformat()


def test_terminal_statuses():
    assert estimate_delivery('DELIVERED', START.isoformat(), 20, 6, START) == START.isoformat()
    assert estimate_delivery('CANCELLED', START.isoformat(), 20, 6, START) is None


def test_remaining_minutes_rounding_and_overdue():
    assert remaining_minutes((START + timedelta(seconds=61)).isoformat(), START) == 2
    assert remaining_minutes((START - timedelta(seconds=1)).isoformat(), START) == 0
    assert remaining_minutes(None, START) is None

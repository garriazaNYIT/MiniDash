# Import datetime, timedelta, timezone from datetime.
from datetime import datetime, timedelta, timezone

# Import pytest for use in this module.
import pytest

# Import estimate_delivery, remaining_minutes from app.eta.
from app.eta import estimate_delivery, remaining_minutes


# Set START to datetime(2026, 10, 30, 12, tzinfo=timezone.utc).
START = datetime(2026, 10, 30, 12, tzinfo=timezone.utc)


# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('distance,travel', [(0, 0), (6, 12), (0.01, 1), (0.5, 1), (0.51, 2)])
# Define the test for initial preparation and rounded travel.
def test_initial_preparation_and_rounded_travel(distance, travel):

    # Verify that estimate_delivery('PLACED', START.isoformat(), 20, distance, START)
    # == (START + timedelta(minutes=20 + travel)).isoformat().
    assert estimate_delivery('PLACED', START.isoformat(), 20, distance, START) == (

        # Supply the remaining arguments or values for the expression above.
        START + timedelta(minutes=20 + travel)).isoformat()


# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('elapsed,remaining', [(5, 15), (25, 0)])
# Define the test for preparing subtracts elapsed time.
def test_preparing_subtracts_elapsed_time(elapsed, remaining):

    # Set now to START + timedelta(minutes=elapsed).
    now = START + timedelta(minutes=elapsed)

    # Verify that estimate_delivery('PREPARING', START.isoformat(), 20, 6, now) ==
    # (now + timedelta(minutes=remaining + 12)).isoformat().
    assert estimate_delivery('PREPARING', START.isoformat(), 20, 6, now) == (

        # Supply the remaining arguments or values for the expression above.
        now + timedelta(minutes=remaining + 12)).isoformat()


# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('status', ['READY', 'PICKED_UP'])
# Define the test for delivery phases exclude preparation.
def test_delivery_phases_exclude_preparation(status):

    # Verify that estimate_delivery(status, START.isoformat(), 20, 6, START) == (START
    # + timedelta(minutes=12)).isoformat().
    assert estimate_delivery(status, START.isoformat(), 20, 6, START) == (

        # Supply the remaining arguments or values for the expression above.
        START + timedelta(minutes=12)).isoformat()


# Define the test for terminal statuses.
def test_terminal_statuses():

    # Verify that estimate_delivery('DELIVERED', START.isoformat(), 20, 6, START) ==
    # START.isoformat().
    assert estimate_delivery('DELIVERED', START.isoformat(), 20, 6, START) == START.isoformat()

    # Verify that estimate_delivery('CANCELLED', START.isoformat(), 20, 6, START) is
    # None.
    assert estimate_delivery('CANCELLED', START.isoformat(), 20, 6, START) is None


# Define the test for remaining minutes rounding and overdue.
def test_remaining_minutes_rounding_and_overdue():

    # Verify that remaining_minutes((START + timedelta(seconds=61)).isoformat(),
    # START) == 2.
    assert remaining_minutes((START + timedelta(seconds=61)).isoformat(), START) == 2

    # Verify that remaining_minutes((START - timedelta(seconds=1)).isoformat(), START)
    # == 0.
    assert remaining_minutes((START - timedelta(seconds=1)).isoformat(), START) == 0

    # Verify that remaining_minutes(None, START) is None.
    assert remaining_minutes(None, START) is None

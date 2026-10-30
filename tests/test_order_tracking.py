"""Business-policy tests; HTTP/persistence integration belongs to slice 2."""

# Import product from itertools.
from itertools import product

# Import pytest for use in this module.
import pytest

# Import OrderStatus, is_status_change from app.order_tracking.
from app.order_tracking import OrderStatus, is_status_change


# Explicit contract, independent of the implementation transition collection.
# Set STATUSES to ('PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED', 'CANCELLED').
STATUSES = ('PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED', 'CANCELLED')

# Build the value below and store it in FORWARD.
FORWARD = {

    # Supply the remaining arguments or values for the expression above.
    ('PLACED', 'PREPARING'),

    # Supply the remaining arguments or values for the expression above.
    ('PREPARING', 'READY'),

    # Supply the remaining arguments or values for the expression above.
    ('READY', 'PICKED_UP'),

    # Supply the remaining arguments or values for the expression above.
    ('PICKED_UP', 'DELIVERED'),

    # Supply the remaining arguments or values for the expression above.
    ('PLACED', 'CANCELLED'),

# Finish the expression started above.
}


# Define the test for status vocabulary.
def test_status_vocabulary():

    # Verify that {status.value for status in OrderStatus} == set(STATUSES).
    assert {status.value for status in OrderStatus} == set(STATUSES)


# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('current,requested', product(STATUSES, repeat=2))
# Define the test for every recognized transition.
def test_every_recognized_transition(current, requested):

    # Run this branch when current == requested.
    if current == requested:

        # Verify that is_status_change(current, requested) is False.
        assert is_status_change(current, requested) is False
    # Otherwise check this additional condition.
    elif (current, requested) in FORWARD:

        # Verify that is_status_change(current, requested) is True.
        assert is_status_change(current, requested) is True
    # Handle the alternative case or the successful try-block result.
    else:

        # Enter pytest.raises(ValueError, match='Invalid status transition') and
        # run the indented block with its cleanup behavior.
        with pytest.raises(ValueError, match='Invalid status transition'):

            # Call is_status_change(current, requested).
            is_status_change(current, requested)


# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('invalid', ['pending', 'preparing', 'placed', 'UNKNOWN', '', None, 1])
# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('position', ['current', 'requested', 'both'])
# Define the test for unknown statuses are rejected even when repeated.
def test_unknown_statuses_are_rejected_even_when_repeated(invalid, position):

    # Set current to invalid if position in ('current', 'both') else 'PLACED'.
    current = invalid if position in ('current', 'both') else 'PLACED'

    # Set requested to invalid if position in ('requested', 'both') else 'PREPARING'.
    requested = invalid if position in ('requested', 'both') else 'PREPARING'

    # Enter pytest.raises(ValueError) and run the indented block with its cleanup
    # behavior.
    with pytest.raises(ValueError):

        # Call is_status_change(current, requested).
        is_status_change(current, requested)


# Define the test for enum members are accepted.
def test_enum_members_are_accepted():

    # Verify that is_status_change(OrderStatus.PLACED, OrderStatus.PREPARING) is True.
    assert is_status_change(OrderStatus.PLACED, OrderStatus.PREPARING) is True

    # Verify that is_status_change(OrderStatus.CANCELLED, OrderStatus.CANCELLED) is
    # False.
    assert is_status_change(OrderStatus.CANCELLED, OrderStatus.CANCELLED) is False

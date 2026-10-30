"""Business-policy tests; HTTP/persistence integration belongs to slice 2."""
from itertools import product

import pytest

from app.order_tracking import OrderStatus, is_status_change


# Explicit contract, independent of the implementation transition collection.
STATUSES = ('PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED', 'CANCELLED')
FORWARD = {
    ('PLACED', 'PREPARING'),
    ('PREPARING', 'READY'),
    ('READY', 'PICKED_UP'),
    ('PICKED_UP', 'DELIVERED'),
    ('PLACED', 'CANCELLED'),
}


def test_status_vocabulary():
    assert {status.value for status in OrderStatus} == set(STATUSES)


@pytest.mark.parametrize('current,requested', product(STATUSES, repeat=2))
def test_every_recognized_transition(current, requested):
    if current == requested:
        assert is_status_change(current, requested) is False
    elif (current, requested) in FORWARD:
        assert is_status_change(current, requested) is True
    else:
        with pytest.raises(ValueError, match='Invalid status transition'):
            is_status_change(current, requested)


@pytest.mark.parametrize('invalid', ['pending', 'preparing', 'placed', 'UNKNOWN', '', None, 1])
@pytest.mark.parametrize('position', ['current', 'requested', 'both'])
def test_unknown_statuses_are_rejected_even_when_repeated(invalid, position):
    current = invalid if position in ('current', 'both') else 'PLACED'
    requested = invalid if position in ('requested', 'both') else 'PREPARING'
    with pytest.raises(ValueError):
        is_status_change(current, requested)


def test_enum_members_are_accepted():
    assert is_status_change(OrderStatus.PLACED, OrderStatus.PREPARING) is True
    assert is_status_change(OrderStatus.CANCELLED, OrderStatus.CANCELLED) is False

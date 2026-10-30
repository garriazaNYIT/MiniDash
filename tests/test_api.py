"""Exercise the real ASGI app using only the standard library and pytest."""
import asyncio
import json
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from app.main import create_app
from app.repository import Repository
from app.services import OrderService
from app.schemas import OrderInput


@pytest.fixture
def api(tmp_path):
    return make_api(create_app(tmp_path / 'test.db'))


def make_api(app):

    def request(method, path, body=None):
        async def run():
            messages = []
            received = False

            async def receive():
                nonlocal received
                if not received:
                    received = True
                    return {'type': 'http.request', 'body': json.dumps(body).encode()
                            if body is not None else b'', 'more_body': False}
                await asyncio.Event().wait()

            async def send(message):
                messages.append(message)

            scope = {
                'type': 'http', 'asgi': {'version': '3.0', 'spec_version': '2.3'},
                'http_version': '1.1', 'method': method, 'scheme': 'http',
                'path': path, 'raw_path': path.encode(), 'query_string': b'',
                'root_path': '', 'headers': [(b'content-type', b'application/json')],
                'client': ('127.0.0.1', 1234), 'server': ('test', 80),
            }
            async with app.router.lifespan_context(app):
                await app(scope, receive, send)
            status = next(m['status'] for m in messages if m['type'] == 'http.response.start')
            content = b''.join(m.get('body', b'') for m in messages
                               if m['type'] == 'http.response.body')
            return status, json.loads(content)

        return asyncio.run(run())

    return request


def order_payload(**changes):
    return {'restaurant_id': 1, 'address': '123 Main Street', 'delivery_distance_km': 6,
            'items': [{'menu_item_id': 1, 'quantity': 2},
                      {'menu_item_id': 2, 'quantity': 1}], **changes}


def test_restaurants_seeded_idempotently(api):
    status, restaurants = api('GET', '/restaurants')
    assert status == 200
    assert len(restaurants) == 5
    assert restaurants[0]['name'] == 'Pizza Corner'
    assert api('GET', '/restaurants') == (status, restaurants)


def test_menu(api):
    status, menu = api('GET', '/restaurants/1/menu')
    assert status == 200
    assert len(menu) == 2
    assert all(item['restaurant_id'] == 1 for item in menu)
    assert menu[0]['price_cents'] == 1200
    assert api('GET', '/restaurants/999/menu')[0] == 404


def test_create_and_get_order(api):
    status, order = api('POST', '/orders', order_payload())
    assert status == 201
    assert order['total_cents'] == 2900
    assert order['status'] == 'PLACED'
    assert order['created_at'].endswith('+00:00')
    assert order['items'][0] == {'menu_item_id': 1, 'quantity': 2, 'unit_price_cents': 1200}
    assert api('GET', f"/orders/{order['id']}") == (200, order)
    assert api('GET', '/orders/999')[0] == 404


@pytest.mark.parametrize('changes,expected', [
    ({'restaurant_id': 999}, 404),
    ({'items': []}, 422),
    ({'address': '   '}, 422),
    ({'items': [{'menu_item_id': 999, 'quantity': 1}]}, 422),
    ({'items': [{'menu_item_id': 3, 'quantity': 1}]}, 422),
    ({'items': [{'menu_item_id': 1, 'quantity': 0}]}, 422),
    ({'items': [{'menu_item_id': 1, 'quantity': -1}]}, 422),
    ({'items': [{'menu_item_id': 1, 'quantity': 1.5}]}, 422),
    ({'items': [{'menu_item_id': 1, 'quantity': True}]}, 422),
    ({'items': [{'menu_item_id': 1, 'quantity': 10**20}]}, 422),
    ({'items': [{'menu_item_id': 1, 'quantity': 1}] * 2}, 422),
])
def test_invalid_order_does_not_persist(api, changes, expected):
    assert api('POST', '/orders', order_payload(**changes))[0] == expected
    assert api('GET', '/orders/1')[0] == 404


def test_status_lifecycle(api):
    _, order = api('POST', '/orders', order_payload())
    path = f"/orders/{order['id']}/status"
    assert api('PATCH', path, {'status': 'DELIVERED'})[0] == 409
    assert api('PATCH', path, {'status': 'unknown'})[0] == 422
    for status in ['PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED']:
        code, updated = api('PATCH', path, {'status': status})
        assert code == 200
        assert updated['status'] == status
    assert api('PATCH', path, {'status': 'CANCELLED'})[0] == 409
    assert api('GET', f"/orders/{order['id']}")[1]['status'] == 'DELIVERED'
    assert api('PATCH', '/orders/999/status', {'status': 'PREPARING'})[0] == 404


def test_cancellation(api):
    api('POST', '/orders', order_payload())
    assert api('PATCH', '/orders/1/status', {'status': 'CANCELLED'})[1]['status'] == 'CANCELLED'
    assert api('PATCH', '/orders/1/status', {'status': 'PREPARING'})[0] == 409


def test_required_fields_and_invalid_path(api):
    assert api('POST', '/orders', {})[0] == 422
    assert api('GET', '/orders/not-an-id')[0] == 422
    assert api('GET', '/restaurants/not-an-id/menu')[0] == 422


def history_at(path, order_id=1):
    repo = Repository(path)
    with repo.connect() as db:
        return repo.status_history(db, order_id)


def test_history_lifecycle_noops_and_restart(api, tmp_path):
    _, order = api('POST', '/orders', order_payload())
    path = tmp_path / 'test.db'
    initial = history_at(path)
    assert initial == [{'status': 'PLACED', 'changed_at': order['created_at']}]
    statuses = ['PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED']
    for index, status in enumerate(statuses):
        assert api('PATCH', '/orders/1/status', {'status': status})[0] == 200
        before = history_at(path)
        assert [event['status'] for event in before] == statuses[:index + 1]
        for _ in range(2):
            assert api('PATCH', '/orders/1/status', {'status': status})[0] == 200
        assert history_at(path) == before
    times = [datetime.fromisoformat(event['changed_at']) for event in before]
    assert all(value.utcoffset() == timedelta(0) for value in times)
    assert times == sorted(times)
    restarted = create_app(path)
    repo = restarted.state.repository
    repo.initialize()
    repo.initialize()
    with repo.connect() as db:
        assert repo.status_history(db, 1) == before
        assert repo.order(db, 1)['status'] == 'DELIVERED'


@pytest.mark.parametrize('current', ['PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED', 'CANCELLED'])
def test_history_invalid_transitions_and_order_isolation(api, tmp_path, current):
    api('POST', '/orders', order_payload())
    api('POST', '/orders', order_payload())
    sequence = ['PREPARING', 'READY', 'PICKED_UP', 'DELIVERED']
    if current == 'CANCELLED':
        sequence = ['CANCELLED']
    elif current == 'PLACED':
        sequence = []
    else:
        sequence = sequence[:sequence.index(current) + 1]
    for status in sequence:
        assert api('PATCH', '/orders/1/status', {'status': status})[0] == 200
    before_order = api('GET', '/orders/1')
    before_history = history_at(tmp_path / 'test.db')
    valid_next = {'PLACED': {'PREPARING', 'CANCELLED'}, 'PREPARING': {'READY'},
                  'READY': {'PICKED_UP'}, 'PICKED_UP': {'DELIVERED'}}
    for target in ['PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED', 'CANCELLED']:
        if target == current:
            assert api('PATCH', '/orders/1/status', {'status': target})[0] == 200
        elif target not in valid_next.get(current, set()):
            assert api('PATCH', '/orders/1/status', {'status': target})[0] == 409
        else:
            continue
        assert api('GET', '/orders/1') == before_order
        assert history_at(tmp_path / 'test.db') == before_history
    for target in ['pending', 'UNKNOWN']:
        assert api('PATCH', '/orders/1/status', {'status': target})[0] == 422
    assert api('PATCH', '/orders/999/status', {'status': 'PREPARING'})[0] == 404
    assert history_at(tmp_path / 'test.db') == before_history
    assert [event['status'] for event in history_at(tmp_path / 'test.db', 2)] == ['PLACED']


@pytest.mark.parametrize('operation', ['create', 'transition'])
def test_history_write_failure_rolls_back_entire_operation(tmp_path, monkeypatch, operation):
    repo = Repository(tmp_path / 'atomic.db')
    repo.initialize()
    service = OrderService(repo)
    payload = OrderInput(**order_payload())
    if operation == 'transition':
        service.create(payload)
    before = history_at(repo.path)

    def fail_history(*args):
        raise sqlite3.IntegrityError('simulated history failure')

    monkeypatch.setattr(Repository, 'append_status_history', staticmethod(fail_history))
    with pytest.raises(sqlite3.IntegrityError, match='simulated history failure'):
        if operation == 'create':
            service.create(payload)
        else:
            service.change_status(1, 'PREPARING')
    assert history_at(repo.path) == before
    with repo.connect() as db:
        if operation == 'create':
            assert repo.order(db, 1) is None
            assert db.execute('SELECT COUNT(*) FROM order_items').fetchone()[0] == 0
        else:
            assert repo.order(db, 1)['status'] == 'PLACED'


def test_tracking_initial_order(api):
    _, order = api('POST', '/orders', order_payload())
    assert api('GET', '/orders/1/tracking') == (200, {
        'order_id': 1,
        'status': 'PLACED',
        'history': [{'status': 'PLACED', 'changed_at': order['created_at']}],
        'estimated_delivery_at': order['estimated_delivery_at'],
        'eta_updated_at': order['eta_updated_at'],
        'remaining_minutes': 32,
    })


@pytest.mark.parametrize('distance', [-1, 'far', True, None, 1e300])
def test_invalid_distance_does_not_create_order(api, distance):
    assert api('POST', '/orders', order_payload(delivery_distance_km=distance))[0] == 422
    assert api('GET', '/orders/1')[0] == 404


def test_distance_required(api):
    payload = order_payload()
    del payload['delivery_distance_km']
    assert api('POST', '/orders', payload)[0] == 422


@pytest.mark.parametrize('distance', [float('nan'), float('inf'), float('-inf')])
def test_nonfinite_distances_rejected(distance):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        OrderInput(**order_payload(delivery_distance_km=distance))


def test_eta_write_failure_rolls_back_status_and_history(api, tmp_path, monkeypatch):
    api('POST', '/orders', order_payload())
    before = api('GET', '/orders/1')
    history = history_at(tmp_path / 'test.db')

    def fail(*args):
        raise sqlite3.IntegrityError('ETA write failed')

    monkeypatch.setattr(Repository, 'update_eta', staticmethod(fail))
    with pytest.raises(sqlite3.IntegrityError, match='ETA write failed'):
        api('PATCH', '/orders/1/status', {'status': 'PREPARING'})
    assert api('GET', '/orders/1') == before
    assert history_at(tmp_path / 'test.db') == history


def test_eta_status_changes_noops_and_persistence(api, tmp_path, monkeypatch):
    import app.services as services

    class Clock(datetime):
        current = datetime(2026, 10, 30, 12, tzinfo=timezone.utc)

        @classmethod
        def now(cls, tz=None):
            return cls.current

    monkeypatch.setattr(services, 'datetime', Clock)
    _, order = api('POST', '/orders', order_payload())
    assert order['estimated_delivery_at'] == '2026-10-30T12:32:00+00:00'
    for status, minute, expected in [('PREPARING', 5, 32), ('READY', 10, 22),
                                     ('PICKED_UP', 15, 27), ('DELIVERED', 25, 25)]:
        Clock.current = Clock.current.replace(minute=minute)
        code, order = api('PATCH', '/orders/1/status', {'status': status})
        assert code == 200
        assert order['estimated_delivery_at'] == Clock.current.replace(minute=expected).isoformat()
        assert order['eta_updated_at'] == Clock.current.isoformat()
        Clock.current += timedelta(seconds=10)
        assert api('PATCH', '/orders/1/status', {'status': status}) == (200, order)
        assert api('PATCH', '/orders/1/status', {'status': 'PLACED'})[0] == 409
        assert api('GET', '/orders/1')[1] == order
    restarted = make_api(create_app(tmp_path / 'test.db'))
    tracking = restarted('GET', '/orders/1/tracking')[1]
    assert tracking['estimated_delivery_at'] == order['estimated_delivery_at']
    assert tracking['eta_updated_at'] == order['eta_updated_at']
    assert tracking['remaining_minutes'] == 0
    api('POST', '/orders', order_payload(delivery_distance_km=0))
    cancelled = api('PATCH', '/orders/2/status', {'status': 'CANCELLED'})[1]
    assert cancelled['estimated_delivery_at'] is None
    assert api('GET', '/orders/2/tracking')[1]['remaining_minutes'] is None


def test_tracking_missing_and_invalid_order(api):
    assert api('GET', '/orders/999/tracking') == (404, {'detail': 'Order not found'})
    assert api('GET', '/orders/not-an-id/tracking')[0] == 422


def test_tracking_ordered_history_and_persistence(api, tmp_path):
    api('POST', '/orders', order_payload())
    api('POST', '/orders', order_payload())
    statuses = ['PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED']
    for status in statuses[1:]:
        assert api('PATCH', '/orders/1/status', {'status': status})[0] == 200
    code, tracking = api('GET', '/orders/1/tracking')
    assert code == 200
    assert set(tracking) == {'order_id', 'status', 'history', 'estimated_delivery_at', 'eta_updated_at', 'remaining_minutes'}
    assert tracking['status'] == 'DELIVERED'
    assert [event['status'] for event in tracking['history']] == statuses
    times = [datetime.fromisoformat(event['changed_at']) for event in tracking['history']]
    assert times == sorted(times)
    assert all(value.utcoffset() == timedelta(0) for value in times)
    assert tracking['history'] == history_at(tmp_path / 'test.db')
    restarted_api = make_api(create_app(tmp_path / 'test.db'))
    assert restarted_api('GET', '/orders/1/tracking') == (200, tracking)
    assert [event['status'] for event in restarted_api('GET', '/orders/2/tracking')[1]['history']] == ['PLACED']


def test_tracking_stable_order_for_equal_timestamps(api, tmp_path):
    api('POST', '/orders', order_payload())
    api('PATCH', '/orders/1/status', {'status': 'PREPARING'})
    api('PATCH', '/orders/1/status', {'status': 'READY'})
    with Repository(tmp_path / 'test.db').connect() as db:
        db.execute("UPDATE order_status_history SET changed_at = '2026-10-30T12:00:00+00:00'")
    tracking = api('GET', '/orders/1/tracking')[1]
    assert [event['status'] for event in tracking['history']] == ['PLACED', 'PREPARING', 'READY']
    assert all(event['changed_at'] == '2026-10-30T12:00:00+00:00' for event in tracking['history'])


@pytest.mark.parametrize('terminal', ['DELIVERED', 'CANCELLED'])
def test_tracking_is_read_only(api, tmp_path, terminal):
    api('POST', '/orders', order_payload())
    sequence = ['PREPARING', 'READY', 'PICKED_UP', 'DELIVERED'] if terminal == 'DELIVERED' else ['CANCELLED']
    for status in sequence:
        api('PATCH', '/orders/1/status', {'status': status})
    repo = Repository(tmp_path / 'test.db')
    with repo.connect() as db:
        before = list(db.iterdump())
    first = api('GET', '/orders/1/tracking')
    for _ in range(3):
        assert api('GET', '/orders/1/tracking') == first
    assert first[1]['status'] == terminal
    with repo.connect() as db:
        assert list(db.iterdump()) == before

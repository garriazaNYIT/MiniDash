"""Exercise the real ASGI app using only the standard library and pytest."""
import asyncio
import json

import pytest

from app.main import create_app


@pytest.fixture
def api(tmp_path):
    app = create_app(tmp_path / 'test.db')

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
    return {'restaurant_id': 1, 'address': '123 Main Street',
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
    assert order['status'] == 'pending'
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
    assert api('PATCH', path, {'status': 'delivered'})[0] == 409
    assert api('PATCH', path, {'status': 'unknown'})[0] == 422
    for status in ['pending', 'preparing', 'out_for_delivery', 'delivered']:
        code, updated = api('PATCH', path, {'status': status})
        assert code == 200
        assert updated['status'] == status
    assert api('PATCH', path, {'status': 'cancelled'})[0] == 409
    assert api('GET', f"/orders/{order['id']}")[1]['status'] == 'delivered'
    assert api('PATCH', '/orders/999/status', {'status': 'preparing'})[0] == 404


def test_cancellation(api):
    api('POST', '/orders', order_payload())
    assert api('PATCH', '/orders/1/status', {'status': 'cancelled'})[1]['status'] == 'cancelled'
    assert api('PATCH', '/orders/1/status', {'status': 'preparing'})[0] == 409


def test_required_fields_and_invalid_path(api):
    assert api('POST', '/orders', {})[0] == 422
    assert api('GET', '/orders/not-an-id')[0] == 422
    assert api('GET', '/restaurants/not-an-id/menu')[0] == 422

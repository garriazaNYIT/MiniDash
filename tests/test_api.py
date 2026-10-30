"""Exercise the real ASGI app using only the standard library and pytest."""

# Import asyncio for use in this module.
import asyncio

# Import json for use in this module.
import json

# Import sqlite3 for use in this module.
import sqlite3

# Import datetime, timedelta, timezone from datetime.
from datetime import datetime, timedelta, timezone

# Import pytest for use in this module.
import pytest

# Import create_app from app.main.
from app.main import create_app

# Import Repository from app.repository.
from app.repository import Repository

# Import OrderService from app.services.
from app.services import OrderService

# Import OrderInput from app.schemas.
from app.schemas import OrderInput


# Apply this decorator to configure the function defined below.
@pytest.fixture
# Define api.
def api(tmp_path):

    # Return make_api(create_app(tmp_path / 'test.db')).
    return make_api(create_app(tmp_path / 'test.db'))


# Define make api.
def make_api(app):

    # Define request.
    def request(method, path, body=None):

        # Define run.
        async def run():

            # Set messages to [].
            messages = []

            # Set received to False.
            received = False

            # Define receive.
            async def receive():

                # Use the enclosing function variable received.
                nonlocal received

                # Run this branch when not received.
                if not received:

                    # Set received to True.
                    received = True

                    # Build and return the response fields below.
                    return {'type': 'http.request', 'body': json.dumps(body).encode()

                            # Supply the remaining arguments
                            # or values for the expression
                            # above.
                            if body is not None else b'', 'more_body': False}

                # Wait for asyncio.Event().wait() to finish.
                await asyncio.Event().wait()

            # Define send.
            async def send(message):

                # Call messages.append(message).
                messages.append(message)

            # Build the value below and store it in scope.
            scope = {

                # Provide the type field.
                'type': 'http', 'asgi': {'version': '3.0', 'spec_version': '2.3'},

                # Provide the http version field.
                'http_version': '1.1', 'method': method, 'scheme': 'http',

                # Provide the path field.
                'path': path, 'raw_path': path.encode(), 'query_string': b'',

                # Provide the root path field.
                'root_path': '', 'headers': [(b'content-type', b'application/json')],

                # Provide the client field.
                'client': ('127.0.0.1', 1234), 'server': ('test', 80),

            # Finish the expression started above.
            }

            # Enter app.router.lifespan_context(app) and run the indented
            # block with its cleanup behavior.
            async with app.router.lifespan_context(app):

                # Wait for app(scope, receive, send) to finish.
                await app(scope, receive, send)

            # Set status to next((m['status'] for m in messages if m['type']
            # == 'http.response.start')).
            status = next(m['status'] for m in messages if m['type'] == 'http.response.start')

            # Set content to b''.join((m.get('body', b'') for m in messages if
            # m['type'] == 'http.response.body')).
            content = b''.join(m.get('body', b'') for m in messages

                               # Supply the remaining
                               # arguments or values for
                               # the expression above.
                               if m['type'] == 'http.response.body')

            # Return (status, json.loads(content)).
            return status, json.loads(content)

        # Return asyncio.run(run()).
        return asyncio.run(run())

    # Return request.
    return request


# Define order payload.
def order_payload(**changes):

    # Build and return the response fields below.
    return {'restaurant_id': 1, 'address': '123 Main Street', 'delivery_distance_km': 6,

            # Provide the items field.
            'items': [{'menu_item_id': 1, 'quantity': 2},

                      # Supply the remaining arguments or values for
                      # the expression above.
                      {'menu_item_id': 2, 'quantity': 1}], **changes}


# Define the test for restaurants seeded idempotently.
def test_restaurants_seeded_idempotently(api):

    # Set (status, restaurants) to api('GET', '/restaurants').
    status, restaurants = api('GET', '/restaurants')

    # Verify that status == 200.
    assert status == 200

    # Verify that len(restaurants) == 5.
    assert len(restaurants) == 5

    # Verify that restaurants[0]['name'] == 'Pizza Corner'.
    assert restaurants[0]['name'] == 'Pizza Corner'

    # Verify that api('GET', '/restaurants') == (status, restaurants).
    assert api('GET', '/restaurants') == (status, restaurants)


# Define the test for menu.
def test_menu(api):

    # Set (status, menu) to api('GET', '/restaurants/1/menu').
    status, menu = api('GET', '/restaurants/1/menu')

    # Verify that status == 200.
    assert status == 200

    # Verify that len(menu) == 2.
    assert len(menu) == 2

    # Verify that all((item['restaurant_id'] == 1 for item in menu)).
    assert all(item['restaurant_id'] == 1 for item in menu)

    # Verify that menu[0]['price_cents'] == 1200.
    assert menu[0]['price_cents'] == 1200

    # Verify that api('GET', '/restaurants/999/menu')[0] == 404.
    assert api('GET', '/restaurants/999/menu')[0] == 404


# Define the test for create and get order.
def test_create_and_get_order(api):

    # Set (status, order) to api('POST', '/orders', order_payload()).
    status, order = api('POST', '/orders', order_payload())

    # Verify that status == 201.
    assert status == 201

    # Verify that order['total_cents'] == 2900.
    assert order['total_cents'] == 2900

    # Verify that order['status'] == 'PLACED'.
    assert order['status'] == 'PLACED'

    # Verify that order['created_at'].endswith('+00:00').
    assert order['created_at'].endswith('+00:00')

    # Verify that order['items'][0] == {'menu_item_id': 1, 'quantity': 2,
    # 'unit_price_cents': 1200}.
    assert order['items'][0] == {'menu_item_id': 1, 'quantity': 2, 'unit_price_cents': 1200}

    # Verify that api('GET', f"/orders/{order['id']}") == (200, order).
    assert api('GET', f"/orders/{order['id']}") == (200, order)

    # Verify that api('GET', '/orders/999')[0] == 404.
    assert api('GET', '/orders/999')[0] == 404


# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('changes,expected', [
    # Continue the expression above.
    ({'restaurant_id': 999}, 404),

    # Continue the expression above.
    ({'items': []}, 422),

    # Continue the expression above.
    ({'address': '   '}, 422),

    # Continue the expression above.
    ({'items': [{'menu_item_id': 999, 'quantity': 1}]}, 422),

    # Continue the expression above.
    ({'items': [{'menu_item_id': 3, 'quantity': 1}]}, 422),

    # Continue the expression above.
    ({'items': [{'menu_item_id': 1, 'quantity': 0}]}, 422),

    # Continue the expression above.
    ({'items': [{'menu_item_id': 1, 'quantity': -1}]}, 422),

    # Continue the expression above.
    ({'items': [{'menu_item_id': 1, 'quantity': 1.5}]}, 422),

    # Continue the expression above.
    ({'items': [{'menu_item_id': 1, 'quantity': True}]}, 422),

    # Continue the expression above.
    ({'items': [{'menu_item_id': 1, 'quantity': 10**20}]}, 422),

    # Continue the expression above.
    ({'items': [{'menu_item_id': 1, 'quantity': 1}] * 2}, 422),

# Continue the expression above.
])

# Define the test for invalid order does not persist.
def test_invalid_order_does_not_persist(api, changes, expected):

    # Verify that api('POST', '/orders', order_payload(**changes))[0] == expected.
    assert api('POST', '/orders', order_payload(**changes))[0] == expected

    # Verify that api('GET', '/orders/1')[0] == 404.
    assert api('GET', '/orders/1')[0] == 404


# Define the test for status lifecycle.
def test_status_lifecycle(api):

    # Set (_, order) to api('POST', '/orders', order_payload()).
    _, order = api('POST', '/orders', order_payload())

    # Set path to f"/orders/{order['id']}/status".
    path = f"/orders/{order['id']}/status"

    # Verify that api('PATCH', path, {'status': 'DELIVERED'})[0] == 409.
    assert api('PATCH', path, {'status': 'DELIVERED'})[0] == 409

    # Verify that api('PATCH', path, {'status': 'unknown'})[0] == 422.
    assert api('PATCH', path, {'status': 'unknown'})[0] == 422

    # Loop over ['PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED'], assigning
    # each value to status.
    for status in ['PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED']:

        # Set (code, updated) to api('PATCH', path, {'status': status}).
        code, updated = api('PATCH', path, {'status': status})

        # Verify that code == 200.
        assert code == 200

        # Verify that updated['status'] == status.
        assert updated['status'] == status

    # Verify that api('PATCH', path, {'status': 'CANCELLED'})[0] == 409.
    assert api('PATCH', path, {'status': 'CANCELLED'})[0] == 409

    # Verify that api('GET', f"/orders/{order['id']}")[1]['status'] == 'DELIVERED'.
    assert api('GET', f"/orders/{order['id']}")[1]['status'] == 'DELIVERED'

    # Verify that api('PATCH', '/orders/999/status', {'status': 'PREPARING'})[0] ==
    # 404.
    assert api('PATCH', '/orders/999/status', {'status': 'PREPARING'})[0] == 404


# Define the test for cancellation.
def test_cancellation(api):

    # Call api('POST', '/orders', order_payload()).
    api('POST', '/orders', order_payload())

    # Verify that api('PATCH', '/orders/1/status', {'status':
    # 'CANCELLED'})[1]['status'] == 'CANCELLED'.
    assert api('PATCH', '/orders/1/status', {'status': 'CANCELLED'})[1]['status'] == 'CANCELLED'

    # Verify that api('PATCH', '/orders/1/status', {'status': 'PREPARING'})[0] == 409.
    assert api('PATCH', '/orders/1/status', {'status': 'PREPARING'})[0] == 409


# Define the test for required fields and invalid path.
def test_required_fields_and_invalid_path(api):

    # Verify that api('POST', '/orders', {})[0] == 422.
    assert api('POST', '/orders', {})[0] == 422

    # Verify that api('GET', '/orders/not-an-id')[0] == 422.
    assert api('GET', '/orders/not-an-id')[0] == 422

    # Verify that api('GET', '/restaurants/not-an-id/menu')[0] == 422.
    assert api('GET', '/restaurants/not-an-id/menu')[0] == 422


# Define history at.
def history_at(path, order_id=1):

    # Set repo to Repository(path).
    repo = Repository(path)

    # Enter repo.connect() and run the indented block with its cleanup behavior.
    with repo.connect() as db:

        # Return repo.status_history(db, order_id).
        return repo.status_history(db, order_id)


# Define the test for history lifecycle noops and restart.
def test_history_lifecycle_noops_and_restart(api, tmp_path):

    # Set (_, order) to api('POST', '/orders', order_payload()).
    _, order = api('POST', '/orders', order_payload())

    # Set path to tmp_path / 'test.db'.
    path = tmp_path / 'test.db'

    # Set initial to history_at(path).
    initial = history_at(path)

    # Verify that initial == [{'status': 'PLACED', 'changed_at':
    # order['created_at']}].
    assert initial == [{'status': 'PLACED', 'changed_at': order['created_at']}]

    # Set statuses to ['PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED'].
    statuses = ['PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED']

    # Loop over enumerate(statuses), assigning each value to (index, status).
    for index, status in enumerate(statuses):

        # Verify that api('PATCH', '/orders/1/status', {'status': status})[0] ==
        # 200.
        assert api('PATCH', '/orders/1/status', {'status': status})[0] == 200

        # Set before to history_at(path).
        before = history_at(path)

        # Verify that [event['status'] for event in before] == statuses[:index +
        # 1].
        assert [event['status'] for event in before] == statuses[:index + 1]

        # Loop over range(2), assigning each value to _.
        for _ in range(2):

            # Verify that api('PATCH', '/orders/1/status', {'status':
            # status})[0] == 200.
            assert api('PATCH', '/orders/1/status', {'status': status})[0] == 200

        # Verify that history_at(path) == before.
        assert history_at(path) == before

    # Set times to [datetime.fromisoformat(event['changed_at']) for event in before].
    times = [datetime.fromisoformat(event['changed_at']) for event in before]

    # Verify that all((value.utcoffset() == timedelta(0) for value in times)).
    assert all(value.utcoffset() == timedelta(0) for value in times)

    # Verify that times == sorted(times).
    assert times == sorted(times)

    # Set restarted to create_app(path).
    restarted = create_app(path)

    # Set repo to restarted.state.repository.
    repo = restarted.state.repository

    # Call repo.initialize().
    repo.initialize()

    # Call repo.initialize().
    repo.initialize()

    # Enter repo.connect() and run the indented block with its cleanup behavior.
    with repo.connect() as db:

        # Verify that repo.status_history(db, 1) == before.
        assert repo.status_history(db, 1) == before

        # Verify that repo.order(db, 1)['status'] == 'DELIVERED'.
        assert repo.order(db, 1)['status'] == 'DELIVERED'


# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('current', ['PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED', 'CANCELLED'])
# Define the test for history invalid transitions and order isolation.
def test_history_invalid_transitions_and_order_isolation(api, tmp_path, current):

    # Call api('POST', '/orders', order_payload()).
    api('POST', '/orders', order_payload())

    # Call api('POST', '/orders', order_payload()).
    api('POST', '/orders', order_payload())

    # Set sequence to ['PREPARING', 'READY', 'PICKED_UP', 'DELIVERED'].
    sequence = ['PREPARING', 'READY', 'PICKED_UP', 'DELIVERED']

    # Run this branch when current == 'CANCELLED'.
    if current == 'CANCELLED':

        # Set sequence to ['CANCELLED'].
        sequence = ['CANCELLED']
    # Otherwise check this additional condition.
    elif current == 'PLACED':

        # Set sequence to [].
        sequence = []
    # Handle the alternative case or the successful try-block result.
    else:

        # Set sequence to sequence[:sequence.index(current) + 1].
        sequence = sequence[:sequence.index(current) + 1]

    # Loop over sequence, assigning each value to status.
    for status in sequence:

        # Verify that api('PATCH', '/orders/1/status', {'status': status})[0] ==
        # 200.
        assert api('PATCH', '/orders/1/status', {'status': status})[0] == 200

    # Set before_order to api('GET', '/orders/1').
    before_order = api('GET', '/orders/1')

    # Set before_history to history_at(tmp_path / 'test.db').
    before_history = history_at(tmp_path / 'test.db')

    # Build the value below and store it in valid_next.
    valid_next = {'PLACED': {'PREPARING', 'CANCELLED'}, 'PREPARING': {'READY'},

                  # Supply the remaining arguments or values for the
                  # expression above.
                  'READY': {'PICKED_UP'}, 'PICKED_UP': {'DELIVERED'}}

    # Loop over ['PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED',
    # 'CANCELLED'], assigning each value to target.
    for target in ['PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED', 'CANCELLED']:

        # Run this branch when target == current.
        if target == current:

            # Verify that api('PATCH', '/orders/1/status', {'status':
            # target})[0] == 200.
            assert api('PATCH', '/orders/1/status', {'status': target})[0] == 200
        # Otherwise check this additional condition.
        elif target not in valid_next.get(current, set()):

            # Verify that api('PATCH', '/orders/1/status', {'status':
            # target})[0] == 409.
            assert api('PATCH', '/orders/1/status', {'status': target})[0] == 409
        # Handle the alternative case or the successful try-block result.
        else:

            # Skip to the next loop iteration.
            continue

        # Verify that api('GET', '/orders/1') == before_order.
        assert api('GET', '/orders/1') == before_order

        # Verify that history_at(tmp_path / 'test.db') == before_history.
        assert history_at(tmp_path / 'test.db') == before_history

    # Loop over ['pending', 'UNKNOWN'], assigning each value to target.
    for target in ['pending', 'UNKNOWN']:

        # Verify that api('PATCH', '/orders/1/status', {'status': target})[0] ==
        # 422.
        assert api('PATCH', '/orders/1/status', {'status': target})[0] == 422

    # Verify that api('PATCH', '/orders/999/status', {'status': 'PREPARING'})[0] ==
    # 404.
    assert api('PATCH', '/orders/999/status', {'status': 'PREPARING'})[0] == 404

    # Verify that history_at(tmp_path / 'test.db') == before_history.
    assert history_at(tmp_path / 'test.db') == before_history

    # Verify that [event['status'] for event in history_at(tmp_path / 'test.db', 2)]
    # == ['PLACED'].
    assert [event['status'] for event in history_at(tmp_path / 'test.db', 2)] == ['PLACED']


# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('operation', ['create', 'transition'])
# Define the test for history write failure rolls back entire operation.
def test_history_write_failure_rolls_back_entire_operation(tmp_path, monkeypatch, operation):

    # Set repo to Repository(tmp_path / 'atomic.db').
    repo = Repository(tmp_path / 'atomic.db')

    # Call repo.initialize().
    repo.initialize()

    # Set service to OrderService(repo).
    service = OrderService(repo)

    # Set payload to OrderInput(**order_payload()).
    payload = OrderInput(**order_payload())

    # Run this branch when operation == 'transition'.
    if operation == 'transition':

        # Call service.create(payload).
        service.create(payload)

    # Set before to history_at(repo.path).
    before = history_at(repo.path)

    # Define fail history.
    def fail_history(*args):

        # Raise sqlite3.IntegrityError('simulated history failure') to report the
        # failure.
        raise sqlite3.IntegrityError('simulated history failure')

    # Call monkeypatch.setattr(Repository, 'append_status_history',
    # staticmethod(fail_history)).
    monkeypatch.setattr(Repository, 'append_status_history', staticmethod(fail_history))

    # Enter pytest.raises(sqlite3.IntegrityError, match='simulated history failure')
    # and run the indented block with its cleanup behavior.
    with pytest.raises(sqlite3.IntegrityError, match='simulated history failure'):

        # Run this branch when operation == 'create'.
        if operation == 'create':

            # Call service.create(payload).
            service.create(payload)
        # Handle the alternative case or the successful try-block result.
        else:

            # Call service.change_status(1, 'PREPARING').
            service.change_status(1, 'PREPARING')

    # Verify that history_at(repo.path) == before.
    assert history_at(repo.path) == before

    # Enter repo.connect() and run the indented block with its cleanup behavior.
    with repo.connect() as db:

        # Run this branch when operation == 'create'.
        if operation == 'create':

            # Verify that repo.order(db, 1) is None.
            assert repo.order(db, 1) is None

            # Verify that db.execute('SELECT COUNT(*) FROM
            # order_items').fetchone()[0] == 0.
            assert db.execute('SELECT COUNT(*) FROM order_items').fetchone()[0] == 0
        # Handle the alternative case or the successful try-block result.
        else:

            # Verify that repo.order(db, 1)['status'] == 'PLACED'.
            assert repo.order(db, 1)['status'] == 'PLACED'


# Define the test for tracking initial order.
def test_tracking_initial_order(api):

    # Set (_, order) to api('POST', '/orders', order_payload()).
    _, order = api('POST', '/orders', order_payload())

    # Verify that api('GET', '/orders/1/tracking') == (200, {'order_id': 1, 'status':
    # 'PLACED', 'history': [{'status': 'PLACED', 'changed_at': order['created_at']}],
    # 'estimated_delivery_at':...
    assert api('GET', '/orders/1/tracking') == (200, {

        # Identify the order being tracked.
        'order_id': 1,

        # Include the current order status.
        'status': 'PLACED',

        # Include the ordered status events from SQLite.
        'history': [{'status': 'PLACED', 'changed_at': order['created_at']}],

        # Include the stored delivery estimate.
        'estimated_delivery_at': order['estimated_delivery_at'],

        # Include when the estimate was last updated.
        'eta_updated_at': order['eta_updated_at'],

        # Calculate remaining minutes without updating storage.
        'remaining_minutes': 32,

    # Finish the expression started above.
    })


# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('distance', [-1, 'far', True, None, 1e300])
# Define the test for invalid distance does not create order.
def test_invalid_distance_does_not_create_order(api, distance):

    # Verify that api('POST', '/orders',
    # order_payload(delivery_distance_km=distance))[0] == 422.
    assert api('POST', '/orders', order_payload(delivery_distance_km=distance))[0] == 422

    # Verify that api('GET', '/orders/1')[0] == 404.
    assert api('GET', '/orders/1')[0] == 404


# Define the test for distance required.
def test_distance_required(api):

    # Set payload to order_payload().
    payload = order_payload()

    # Remove payload['delivery_distance_km'].
    del payload['delivery_distance_km']

    # Verify that api('POST', '/orders', payload)[0] == 422.
    assert api('POST', '/orders', payload)[0] == 422


# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('distance', [float('nan'), float('inf'), float('-inf')])
# Define the test for nonfinite distances rejected.
def test_nonfinite_distances_rejected(distance):

    # Import ValidationError from pydantic.
    from pydantic import ValidationError

    # Enter pytest.raises(ValidationError) and run the indented block with its cleanup
    # behavior.
    with pytest.raises(ValidationError):

        # Call OrderInput(**order_payload(delivery_distance_km=distance)).
        OrderInput(**order_payload(delivery_distance_km=distance))


# Define the test for eta write failure rolls back status and history.
def test_eta_write_failure_rolls_back_status_and_history(api, tmp_path, monkeypatch):

    # Call api('POST', '/orders', order_payload()).
    api('POST', '/orders', order_payload())

    # Set before to api('GET', '/orders/1').
    before = api('GET', '/orders/1')

    # Set history to history_at(tmp_path / 'test.db').
    history = history_at(tmp_path / 'test.db')

    # Define fail.
    def fail(*args):

        # Raise sqlite3.IntegrityError('ETA write failed') to report the failure.
        raise sqlite3.IntegrityError('ETA write failed')

    # Call monkeypatch.setattr(Repository, 'update_eta', staticmethod(fail)).
    monkeypatch.setattr(Repository, 'update_eta', staticmethod(fail))

    # Enter pytest.raises(sqlite3.IntegrityError, match='ETA write failed') and run
    # the indented block with its cleanup behavior.
    with pytest.raises(sqlite3.IntegrityError, match='ETA write failed'):

        # Call api('PATCH', '/orders/1/status', {'status': 'PREPARING'}).
        api('PATCH', '/orders/1/status', {'status': 'PREPARING'})

    # Verify that api('GET', '/orders/1') == before.
    assert api('GET', '/orders/1') == before

    # Verify that history_at(tmp_path / 'test.db') == history.
    assert history_at(tmp_path / 'test.db') == history


# Define the test for eta status changes noops and persistence.
def test_eta_status_changes_noops_and_persistence(api, tmp_path, monkeypatch):

    # Import app.services for use in this module.
    import app.services as services

    # Define the Clock class using datetime.
    class Clock(datetime):

        # Set current to datetime(2026, 10, 30, 12, tzinfo=timezone.utc).
        current = datetime(2026, 10, 30, 12, tzinfo=timezone.utc)

        # Apply this decorator to configure the function defined below.
        @classmethod
        # Define now.
        def now(cls, tz=None):

            # Return cls.current.
            return cls.current

    # Call monkeypatch.setattr(services, 'datetime', Clock).
    monkeypatch.setattr(services, 'datetime', Clock)

    # Set (_, order) to api('POST', '/orders', order_payload()).
    _, order = api('POST', '/orders', order_payload())

    # Verify that order['estimated_delivery_at'] == '2026-10-30T12:32:00+00:00'.
    assert order['estimated_delivery_at'] == '2026-10-30T12:32:00+00:00'

    # Loop over [('PREPARING', 5, 32), ('READY', 10, 22), ('PICKED_UP', 15, 27),
    # ('DELIVERED', 25, 25)], assigning each value to (status, minute, expected).
    for status, minute, expected in [('PREPARING', 5, 32), ('READY', 10, 22),

                                     # Supply the
                                     # remaining
                                     # arguments or
                                     # values for the
                                     # expression
                                     # above.
                                     ('PICKED_UP', 15, 27), ('DELIVERED', 25, 25)]:

        # Set Clock.current to Clock.current.replace(minute=minute).
        Clock.current = Clock.current.replace(minute=minute)

        # Set (code, order) to api('PATCH', '/orders/1/status', {'status':
        # status}).
        code, order = api('PATCH', '/orders/1/status', {'status': status})

        # Verify that code == 200.
        assert code == 200

        # Verify that order['estimated_delivery_at'] ==
        # Clock.current.replace(minute=expected).isoformat().
        assert order['estimated_delivery_at'] == Clock.current.replace(minute=expected).isoformat()

        # Verify that order['eta_updated_at'] == Clock.current.isoformat().
        assert order['eta_updated_at'] == Clock.current.isoformat()

        # Update Clock.current using timedelta(seconds=10).
        Clock.current += timedelta(seconds=10)

        # Verify that api('PATCH', '/orders/1/status', {'status': status}) ==
        # (200, order).
        assert api('PATCH', '/orders/1/status', {'status': status}) == (200, order)

        # Verify that api('PATCH', '/orders/1/status', {'status': 'PLACED'})[0] ==
        # 409.
        assert api('PATCH', '/orders/1/status', {'status': 'PLACED'})[0] == 409

        # Verify that api('GET', '/orders/1')[1] == order.
        assert api('GET', '/orders/1')[1] == order

    # Set restarted to make_api(create_app(tmp_path / 'test.db')).
    restarted = make_api(create_app(tmp_path / 'test.db'))

    # Set tracking to restarted('GET', '/orders/1/tracking')[1].
    tracking = restarted('GET', '/orders/1/tracking')[1]

    # Verify that tracking['estimated_delivery_at'] == order['estimated_delivery_at'].
    assert tracking['estimated_delivery_at'] == order['estimated_delivery_at']

    # Verify that tracking['eta_updated_at'] == order['eta_updated_at'].
    assert tracking['eta_updated_at'] == order['eta_updated_at']

    # Verify that tracking['remaining_minutes'] == 0.
    assert tracking['remaining_minutes'] == 0

    # Call api('POST', '/orders', order_payload(delivery_distance_km=0)).
    api('POST', '/orders', order_payload(delivery_distance_km=0))

    # Set cancelled to api('PATCH', '/orders/2/status', {'status': 'CANCELLED'})[1].
    cancelled = api('PATCH', '/orders/2/status', {'status': 'CANCELLED'})[1]

    # Verify that cancelled['estimated_delivery_at'] is None.
    assert cancelled['estimated_delivery_at'] is None

    # Verify that api('GET', '/orders/2/tracking')[1]['remaining_minutes'] is None.
    assert api('GET', '/orders/2/tracking')[1]['remaining_minutes'] is None


# Define the test for tracking missing and invalid order.
def test_tracking_missing_and_invalid_order(api):

    # Verify that api('GET', '/orders/999/tracking') == (404, {'detail': 'Order not
    # found'}).
    assert api('GET', '/orders/999/tracking') == (404, {'detail': 'Order not found'})

    # Verify that api('GET', '/orders/not-an-id/tracking')[0] == 422.
    assert api('GET', '/orders/not-an-id/tracking')[0] == 422


# Define the test for tracking ordered history and persistence.
def test_tracking_ordered_history_and_persistence(api, tmp_path):

    # Call api('POST', '/orders', order_payload()).
    api('POST', '/orders', order_payload())

    # Call api('POST', '/orders', order_payload()).
    api('POST', '/orders', order_payload())

    # Set statuses to ['PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED'].
    statuses = ['PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED']

    # Loop over statuses[1:], assigning each value to status.
    for status in statuses[1:]:

        # Verify that api('PATCH', '/orders/1/status', {'status': status})[0] ==
        # 200.
        assert api('PATCH', '/orders/1/status', {'status': status})[0] == 200

    # Set (code, tracking) to api('GET', '/orders/1/tracking').
    code, tracking = api('GET', '/orders/1/tracking')

    # Verify that code == 200.
    assert code == 200

    # Verify that set(tracking) == {'order_id', 'status', 'history',
    # 'estimated_delivery_at', 'eta_updated_at', 'remaining_minutes'}.
    assert set(tracking) == {'order_id', 'status', 'history', 'estimated_delivery_at', 'eta_updated_at', 'remaining_minutes'}

    # Verify that tracking['status'] == 'DELIVERED'.
    assert tracking['status'] == 'DELIVERED'

    # Verify that [event['status'] for event in tracking['history']] == statuses.
    assert [event['status'] for event in tracking['history']] == statuses

    # Set times to [datetime.fromisoformat(event['changed_at']) for event in
    # tracking['history']].
    times = [datetime.fromisoformat(event['changed_at']) for event in tracking['history']]

    # Verify that times == sorted(times).
    assert times == sorted(times)

    # Verify that all((value.utcoffset() == timedelta(0) for value in times)).
    assert all(value.utcoffset() == timedelta(0) for value in times)

    # Verify that tracking['history'] == history_at(tmp_path / 'test.db').
    assert tracking['history'] == history_at(tmp_path / 'test.db')

    # Set restarted_api to make_api(create_app(tmp_path / 'test.db')).
    restarted_api = make_api(create_app(tmp_path / 'test.db'))

    # Verify that restarted_api('GET', '/orders/1/tracking') == (200, tracking).
    assert restarted_api('GET', '/orders/1/tracking') == (200, tracking)

    # Verify that [event['status'] for event in restarted_api('GET',
    # '/orders/2/tracking')[1]['history']] == ['PLACED'].
    assert [event['status'] for event in restarted_api('GET', '/orders/2/tracking')[1]['history']] == ['PLACED']


# Define the test for tracking stable order for equal timestamps.
def test_tracking_stable_order_for_equal_timestamps(api, tmp_path):

    # Call api('POST', '/orders', order_payload()).
    api('POST', '/orders', order_payload())

    # Call api('PATCH', '/orders/1/status', {'status': 'PREPARING'}).
    api('PATCH', '/orders/1/status', {'status': 'PREPARING'})

    # Call api('PATCH', '/orders/1/status', {'status': 'READY'}).
    api('PATCH', '/orders/1/status', {'status': 'READY'})

    # Enter Repository(tmp_path / 'test.db').connect() and run the indented block with
    # its cleanup behavior.
    with Repository(tmp_path / 'test.db').connect() as db:

        # Call db.execute("UPDATE order_status_history SET changed_at =
        # '2026-10-30T12:00:00+00:00'").
        db.execute("UPDATE order_status_history SET changed_at = '2026-10-30T12:00:00+00:00'")

    # Set tracking to api('GET', '/orders/1/tracking')[1].
    tracking = api('GET', '/orders/1/tracking')[1]

    # Verify that [event['status'] for event in tracking['history']] == ['PLACED',
    # 'PREPARING', 'READY'].
    assert [event['status'] for event in tracking['history']] == ['PLACED', 'PREPARING', 'READY']

    # Verify that all((event['changed_at'] == '2026-10-30T12:00:00+00:00' for event in
    # tracking['history'])).
    assert all(event['changed_at'] == '2026-10-30T12:00:00+00:00' for event in tracking['history'])


# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('terminal', ['DELIVERED', 'CANCELLED'])
# Define the test for tracking is read only.
def test_tracking_is_read_only(api, tmp_path, terminal):

    # Call api('POST', '/orders', order_payload()).
    api('POST', '/orders', order_payload())

    # Set sequence to ['PREPARING', 'READY', 'PICKED_UP', 'DELIVERED'] if terminal ==
    # 'DELIVERED' else ['CANCELLED'].
    sequence = ['PREPARING', 'READY', 'PICKED_UP', 'DELIVERED'] if terminal == 'DELIVERED' else ['CANCELLED']

    # Loop over sequence, assigning each value to status.
    for status in sequence:

        # Call api('PATCH', '/orders/1/status', {'status': status}).
        api('PATCH', '/orders/1/status', {'status': status})

    # Set repo to Repository(tmp_path / 'test.db').
    repo = Repository(tmp_path / 'test.db')

    # Enter repo.connect() and run the indented block with its cleanup behavior.
    with repo.connect() as db:

        # Set before to list(db.iterdump()).
        before = list(db.iterdump())

    # Set first to api('GET', '/orders/1/tracking').
    first = api('GET', '/orders/1/tracking')

    # Loop over range(3), assigning each value to _.
    for _ in range(3):

        # Verify that api('GET', '/orders/1/tracking') == first.
        assert api('GET', '/orders/1/tracking') == first

    # Verify that first[1]['status'] == terminal.
    assert first[1]['status'] == terminal

    # Enter repo.connect() and run the indented block with its cleanup behavior.
    with repo.connect() as db:

        # Verify that list(db.iterdump()) == before.
        assert list(db.iterdump()) == before

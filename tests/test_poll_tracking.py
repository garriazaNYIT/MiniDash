# Import io for use in this module.
import io

# Import json for use in this module.
import json

# Import Mock from unittest.mock.
from unittest.mock import Mock

# Import HTTPError, URLError from urllib.error.
from urllib.error import HTTPError, URLError

# Import pytest for use in this module.
import pytest

# Import poll_tracking from scripts.
from scripts import poll_tracking as client


# Define snapshot.
def snapshot(status='PREPARING', **changes):

    # Build and return the response fields below.
    return {'status': status, 'estimated_delivery_at': '2026-10-30T12:32:00+00:00',

            # Calculate remaining minutes without updating storage.
            'remaining_minutes': 32, **changes}


# Define setup http.
def setup_http(monkeypatch, responses):

    # Define response.
    def response(value):

        # Return value if isinstance(value, BaseException) else
        # io.StringIO(json.dumps(value)).
        return value if isinstance(value, BaseException) else io.StringIO(json.dumps(value))

    # Set http to Mock(side_effect=[response(value) for value in responses]).
    http = Mock(side_effect=[response(value) for value in responses])

    # Set sleep to Mock().
    sleep = Mock()

    # Call monkeypatch.setattr(client, 'urlopen', http).
    monkeypatch.setattr(client, 'urlopen', http)

    # Call monkeypatch.setattr(client.time, 'sleep', sleep).
    monkeypatch.setattr(client.time, 'sleep', sleep)

    # Return (http, sleep).
    return http, sleep


# Define the test for changes only and two second interval.
def test_changes_only_and_two_second_interval(monkeypatch, capsys):

    # Set first to snapshot().
    first = snapshot()

    # Set eta to snapshot(estimated_delivery_at='2026-10-30T12:33:00+00:00').
    eta = snapshot(estimated_delivery_at='2026-10-30T12:33:00+00:00')

    # Set remaining to {**eta, 'remaining_minutes': 31}.
    remaining = {**eta, 'remaining_minutes': 31}

    # Set (http, sleep) to setup_http(monkeypatch, [first, first, eta, remaining,
    # snapshot('DELIVERED')]).
    http, sleep = setup_http(monkeypatch, [first, first, eta, remaining, snapshot('DELIVERED')])

    # Verify that client.poll(7, 'http://example.test/api/') == 0.
    assert client.poll(7, 'http://example.test/api/') == 0

    # Verify that http.call_count == 5.
    assert http.call_count == 5

    # Call http.assert_called_with('http://example.test/api/orders/7/tracking',
    # timeout=10).
    http.assert_called_with('http://example.test/api/orders/7/tracking', timeout=10)

    # Verify that [call.args for call in sleep.call_args_list] == [(2,)] * 4.
    assert [call.args for call in sleep.call_args_list] == [(2,)] * 4

    # Set lines to capsys.readouterr().out.splitlines().
    lines = capsys.readouterr().out.splitlines()

    # Verify that len(lines) == 4.
    assert len(lines) == 4

    # Verify that 'ETA: 2026-10-30T12:33:00+00:00' in lines[1].
    assert 'ETA: 2026-10-30T12:33:00+00:00' in lines[1]

    # Verify that 'Remaining minutes: 31' in lines[2].
    assert 'Remaining minutes: 31' in lines[2]


# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('terminal', ['DELIVERED', 'CANCELLED'])
# Define the test for terminal first response stops.
def test_terminal_first_response_stops(monkeypatch, capsys, terminal):

    # Set (http, sleep) to setup_http(monkeypatch, [snapshot(terminal)]).
    http, sleep = setup_http(monkeypatch, [snapshot(terminal)])

    # Verify that client.poll(1) == 0.
    assert client.poll(1) == 0

    # Verify that terminal in capsys.readouterr().out.
    assert terminal in capsys.readouterr().out

    # Verify that http.call_count == 1.
    assert http.call_count == 1

    # Call sleep.assert_not_called().
    sleep.assert_not_called()


# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('failure', [URLError('offline'), TimeoutError(),
                                    # Continue the
                                    # expression
                                    # above.
                                    ConnectionResetError(), HTTPError('url', 503, 'busy', {}, None)])

# Define the test for temporary failures recover without duplicate display.
def test_temporary_failures_recover_without_duplicate_display(monkeypatch, capsys, failure):

    # Set (http, sleep) to setup_http(monkeypatch, [snapshot(), failure, snapshot(),
    # snapshot('DELIVERED')]).
    http, sleep = setup_http(monkeypatch, [snapshot(), failure, snapshot(), snapshot('DELIVERED')])

    # Verify that client.poll(1) == 0.
    assert client.poll(1) == 0

    # Set output to capsys.readouterr().out.
    output = capsys.readouterr().out

    # Verify that output.count('Status: PREPARING') == 1.
    assert output.count('Status: PREPARING') == 1

    # Verify that 'retrying' in output.lower().
    assert 'retrying' in output.lower()

    # Verify that http.call_count == 4.
    assert http.call_count == 4

    # Verify that sleep.call_count == 3.
    assert sleep.call_count == 3


# Define the test for missing order stops gracefully.
def test_missing_order_stops_gracefully(monkeypatch, capsys):

    # Set (http, sleep) to setup_http(monkeypatch, [HTTPError('url', 404, 'missing',
    # {}, None)]).
    http, sleep = setup_http(monkeypatch, [HTTPError('url', 404, 'missing', {}, None)])

    # Verify that client.poll(99) == 1.
    assert client.poll(99) == 1

    # Verify that 'Order 99 not found' in capsys.readouterr().out.
    assert 'Order 99 not found' in capsys.readouterr().out

    # Call sleep.assert_not_called().
    sleep.assert_not_called()


# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('during_sleep', [True, False])
# Define the test for ctrl c.
def test_ctrl_c(monkeypatch, capsys, during_sleep):

    # Set (http, sleep) to setup_http(monkeypatch, [snapshot() if during_sleep else
    # KeyboardInterrupt()]).
    http, sleep = setup_http(monkeypatch, [snapshot() if during_sleep else KeyboardInterrupt()])

    # Set sleep.side_effect to KeyboardInterrupt.
    sleep.side_effect = KeyboardInterrupt

    # Verify that client.poll(1) == 0.
    assert client.poll(1) == 0

    # Verify that 'Polling stopped' in capsys.readouterr().out.
    assert 'Polling stopped' in capsys.readouterr().out


# Define the test for main arguments.
def test_main_arguments(monkeypatch):

    # Set poll to Mock(return_value=0).
    poll = Mock(return_value=0)

    # Call monkeypatch.setattr(client, 'poll', poll).
    monkeypatch.setattr(client, 'poll', poll)

    # Verify that client.main(['12']) == 0.
    assert client.main(['12']) == 0

    # Call poll.assert_called_with(12, 'http://127.0.0.1:8000').
    poll.assert_called_with(12, 'http://127.0.0.1:8000')

    # Call client.main(['12', '--base-url', 'https://example.test']).
    client.main(['12', '--base-url', 'https://example.test'])

    # Call poll.assert_called_with(12, 'https://example.test').
    poll.assert_called_with(12, 'https://example.test')


# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('args', [['0'], ['no'], ['1', '--base-url', 'file:///tmp']])
# Define the test for invalid cli arguments.
def test_invalid_cli_arguments(args):

    # Enter pytest.raises(SystemExit) and run the indented block with its cleanup
    # behavior.
    with pytest.raises(SystemExit) as error:

        # Call client.main(args).
        client.main(args)

    # Verify that error.value.code == 2.
    assert error.value.code == 2


# Define the test for malformed response.
def test_malformed_response(monkeypatch, capsys):

    # Set (_, sleep) to setup_http(monkeypatch, [{}]).
    _, sleep = setup_http(monkeypatch, [{}])

    # Verify that client.poll(1) == 1.
    assert client.poll(1) == 1

    # Verify that 'Invalid tracking response' in capsys.readouterr().out.
    assert 'Invalid tracking response' in capsys.readouterr().out

    # Call sleep.assert_not_called().
    sleep.assert_not_called()

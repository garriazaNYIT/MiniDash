import io
import json
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

import pytest

from scripts import poll_tracking as client


def snapshot(status='PREPARING', **changes):
    return {'status': status, 'estimated_delivery_at': '2026-10-30T12:32:00+00:00',
            'remaining_minutes': 32, **changes}


def setup_http(monkeypatch, responses):
    def response(value):
        return value if isinstance(value, BaseException) else io.StringIO(json.dumps(value))
    http = Mock(side_effect=[response(value) for value in responses])
    sleep = Mock()
    monkeypatch.setattr(client, 'urlopen', http)
    monkeypatch.setattr(client.time, 'sleep', sleep)
    return http, sleep


def test_changes_only_and_two_second_interval(monkeypatch, capsys):
    first = snapshot()
    eta = snapshot(estimated_delivery_at='2026-10-30T12:33:00+00:00')
    remaining = {**eta, 'remaining_minutes': 31}
    http, sleep = setup_http(monkeypatch, [first, first, eta, remaining, snapshot('DELIVERED')])
    assert client.poll(7, 'http://example.test/api/') == 0
    assert http.call_count == 5
    http.assert_called_with('http://example.test/api/orders/7/tracking', timeout=10)
    assert [call.args for call in sleep.call_args_list] == [(2,)] * 4
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 4
    assert 'ETA: 2026-10-30T12:33:00+00:00' in lines[1]
    assert 'Remaining minutes: 31' in lines[2]


@pytest.mark.parametrize('terminal', ['DELIVERED', 'CANCELLED'])
def test_terminal_first_response_stops(monkeypatch, capsys, terminal):
    http, sleep = setup_http(monkeypatch, [snapshot(terminal)])
    assert client.poll(1) == 0
    assert terminal in capsys.readouterr().out
    assert http.call_count == 1
    sleep.assert_not_called()


@pytest.mark.parametrize('failure', [URLError('offline'), TimeoutError(),
                                    ConnectionResetError(), HTTPError('url', 503, 'busy', {}, None)])
def test_temporary_failures_recover_without_duplicate_display(monkeypatch, capsys, failure):
    http, sleep = setup_http(monkeypatch, [snapshot(), failure, snapshot(), snapshot('DELIVERED')])
    assert client.poll(1) == 0
    output = capsys.readouterr().out
    assert output.count('Status: PREPARING') == 1
    assert 'retrying' in output.lower()
    assert http.call_count == 4
    assert sleep.call_count == 3


def test_missing_order_stops_gracefully(monkeypatch, capsys):
    http, sleep = setup_http(monkeypatch, [HTTPError('url', 404, 'missing', {}, None)])
    assert client.poll(99) == 1
    assert 'Order 99 not found' in capsys.readouterr().out
    sleep.assert_not_called()


@pytest.mark.parametrize('during_sleep', [True, False])
def test_ctrl_c(monkeypatch, capsys, during_sleep):
    http, sleep = setup_http(monkeypatch, [snapshot() if during_sleep else KeyboardInterrupt()])
    sleep.side_effect = KeyboardInterrupt
    assert client.poll(1) == 0
    assert 'Polling stopped' in capsys.readouterr().out


def test_main_arguments(monkeypatch):
    poll = Mock(return_value=0)
    monkeypatch.setattr(client, 'poll', poll)
    assert client.main(['12']) == 0
    poll.assert_called_with(12, 'http://127.0.0.1:8000')
    client.main(['12', '--base-url', 'https://example.test'])
    poll.assert_called_with(12, 'https://example.test')


@pytest.mark.parametrize('args', [['0'], ['no'], ['1', '--base-url', 'file:///tmp']])
def test_invalid_cli_arguments(args):
    with pytest.raises(SystemExit) as error:
        client.main(args)
    assert error.value.code == 2


def test_malformed_response(monkeypatch, capsys):
    _, sleep = setup_http(monkeypatch, [{}])
    assert client.poll(1) == 1
    assert 'Invalid tracking response' in capsys.readouterr().out
    sleep.assert_not_called()

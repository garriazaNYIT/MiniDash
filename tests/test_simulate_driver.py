import io
import json
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

import pytest

from scripts import simulate_driver as client


def setup_http(monkeypatch, responses):
    http = Mock(side_effect=[value if isinstance(value, BaseException)
                            else io.StringIO(json.dumps(value)) for value in responses])
    sleep = Mock()
    monkeypatch.setattr(client, 'urlopen', http)
    monkeypatch.setattr(client.time, 'sleep', sleep)
    return http, sleep


def test_full_lifecycle_requests_and_delays(monkeypatch, capsys):
    statuses = ['PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED']
    responses = [{'status': status} for pair in zip(statuses, statuses[1:]) for status in pair]
    http, sleep = setup_http(monkeypatch, responses)
    assert client.simulate(7, 'http://example.test/api/', 0.5) == 0
    assert [call.args for call in sleep.call_args_list] == [(0.5,)] * 4
    assert http.call_count == 8
    for index, call in enumerate(http.call_args_list):
        request = call.args[0]
        assert call.kwargs == {'timeout': 10}
        if index % 2 == 0:
            assert request.get_method() == 'GET'
            assert request.full_url == 'http://example.test/api/orders/7'
        else:
            assert request.get_method() == 'PATCH'
            assert request.full_url == 'http://example.test/api/orders/7/status'
            assert json.loads(request.data) == {'status': statuses[index // 2 + 1]}
            assert request.get_header('Content-type') == 'application/json'
    assert 'Order 7: DELIVERED' in capsys.readouterr().out


@pytest.mark.parametrize('status', ['PREPARING', 'READY', 'DELIVERED', 'CANCELLED', 'unknown'])
def test_wrong_start_never_patches(monkeypatch, capsys, status):
    http, _ = setup_http(monkeypatch, [{'status': status}])
    assert client.simulate(1, delay=0) == 1
    assert http.call_count == 1
    assert 'Expected PLACED' in capsys.readouterr().out


def test_external_status_change_stops(monkeypatch, capsys):
    http, _ = setup_http(monkeypatch, [{'status': 'PLACED'}, {'status': 'PREPARING'}, {'status': 'DELIVERED'}])
    assert client.simulate(1, delay=0) == 1
    assert http.call_count == 3
    assert 'Expected PREPARING' in capsys.readouterr().out


@pytest.mark.parametrize('failure', [HTTPError('url', 404, 'missing', {}, None),
                                    HTTPError('url', 409, 'conflict', {}, None),
                                    URLError('offline'), TimeoutError('timeout')])
@pytest.mark.parametrize('on_patch', [True, False])
def test_request_failure_stops_without_retry(monkeypatch, capsys, failure, on_patch):
    responses = [{'status': 'PLACED'}, failure] if on_patch else [failure]
    http, _ = setup_http(monkeypatch, responses)
    assert client.simulate(1, delay=0) == 1
    assert http.call_count == len(responses)
    output = capsys.readouterr().out
    assert 'API request failed' in output
    assert 'Order 1: PREPARING' not in output


@pytest.mark.parametrize('response', [{}, [], {'status': None}])
def test_malformed_response_stops(monkeypatch, response):
    http, _ = setup_http(monkeypatch, [response])
    assert client.simulate(1, delay=0) == 1
    assert http.call_count == 1


def test_patch_must_confirm_transition(monkeypatch):
    http, _ = setup_http(monkeypatch, [{'status': 'PLACED'}, {'status': 'PLACED'}])
    assert client.simulate(1, delay=0) == 1
    assert http.call_count == 2


def test_ctrl_c_stops(monkeypatch, capsys):
    http, sleep = setup_http(monkeypatch, [])
    sleep.side_effect = KeyboardInterrupt
    assert client.simulate(1) == 130
    http.assert_not_called()
    assert 'Simulation stopped' in capsys.readouterr().out


def test_cli_defaults_and_options(monkeypatch):
    simulate = Mock(return_value=0)
    monkeypatch.setattr(client, 'simulate', simulate)
    assert client.main(['1']) == 0
    simulate.assert_called_with(1, 'http://127.0.0.1:8000', 3)
    client.main(['2', '--base-url', 'http://example.test', '--delay', '0'])
    simulate.assert_called_with(2, 'http://example.test', 0)


@pytest.mark.parametrize('args', [['0'], ['1', '--delay', '-1'], ['1', '--delay', 'nan'],
                                 ['1', '--delay', 'inf'], ['1', '--base-url', 'file:///tmp']])
def test_invalid_cli_inputs(args):
    with pytest.raises(SystemExit) as error:
        client.main(args)
    assert error.value.code == 2

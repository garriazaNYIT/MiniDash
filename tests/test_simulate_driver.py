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

# Import simulate_driver from scripts.
from scripts import simulate_driver as client


# Define setup http.
def setup_http(monkeypatch, responses):

    # Build the value below and store it in http.
    http = Mock(side_effect=[value if isinstance(value, BaseException)

                            # Supply the remaining arguments
                            # or values for the expression
                            # above.
                            else io.StringIO(json.dumps(value)) for value in responses])

    # Set sleep to Mock().
    sleep = Mock()

    # Call monkeypatch.setattr(client, 'urlopen', http).
    monkeypatch.setattr(client, 'urlopen', http)

    # Call monkeypatch.setattr(client.time, 'sleep', sleep).
    monkeypatch.setattr(client.time, 'sleep', sleep)

    # Return (http, sleep).
    return http, sleep


# Define the test for full lifecycle requests and delays.
def test_full_lifecycle_requests_and_delays(monkeypatch, capsys):

    # Set statuses to ['PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED'].
    statuses = ['PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED']

    # Set responses to [{'status': status} for pair in zip(statuses, statuses[1:]) for
    # status in pair].
    responses = [{'status': status} for pair in zip(statuses, statuses[1:]) for status in pair]

    # Set (http, sleep) to setup_http(monkeypatch, responses).
    http, sleep = setup_http(monkeypatch, responses)

    # Verify that client.simulate(7, 'http://example.test/api/', 0.5) == 0.
    assert client.simulate(7, 'http://example.test/api/', 0.5) == 0

    # Verify that [call.args for call in sleep.call_args_list] == [(0.5,)] * 4.
    assert [call.args for call in sleep.call_args_list] == [(0.5,)] * 4

    # Verify that http.call_count == 8.
    assert http.call_count == 8

    # Loop over enumerate(http.call_args_list), assigning each value to (index, call).
    for index, call in enumerate(http.call_args_list):

        # Set request to call.args[0].
        request = call.args[0]

        # Verify that call.kwargs == {'timeout': 10}.
        assert call.kwargs == {'timeout': 10}

        # Run this branch when index % 2 == 0.
        if index % 2 == 0:

            # Verify that request.get_method() == 'GET'.
            assert request.get_method() == 'GET'

            # Verify that request.full_url ==
            # 'http://example.test/api/orders/7'.
            assert request.full_url == 'http://example.test/api/orders/7'
        # Handle the alternative case or the successful try-block result.
        else:

            # Verify that request.get_method() == 'PATCH'.
            assert request.get_method() == 'PATCH'

            # Verify that request.full_url ==
            # 'http://example.test/api/orders/7/status'.
            assert request.full_url == 'http://example.test/api/orders/7/status'

            # Verify that json.loads(request.data) == {'status':
            # statuses[index // 2 + 1]}.
            assert json.loads(request.data) == {'status': statuses[index // 2 + 1]}

            # Verify that request.get_header('Content-type') ==
            # 'application/json'.
            assert request.get_header('Content-type') == 'application/json'

    # Verify that 'Order 7: DELIVERED' in capsys.readouterr().out.
    assert 'Order 7: DELIVERED' in capsys.readouterr().out


# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('status', ['PREPARING', 'READY', 'DELIVERED', 'CANCELLED', 'unknown'])
# Define the test for wrong start never patches.
def test_wrong_start_never_patches(monkeypatch, capsys, status):

    # Set (http, _) to setup_http(monkeypatch, [{'status': status}]).
    http, _ = setup_http(monkeypatch, [{'status': status}])

    # Verify that client.simulate(1, delay=0) == 1.
    assert client.simulate(1, delay=0) == 1

    # Verify that http.call_count == 1.
    assert http.call_count == 1

    # Verify that 'Expected PLACED' in capsys.readouterr().out.
    assert 'Expected PLACED' in capsys.readouterr().out


# Define the test for external status change stops.
def test_external_status_change_stops(monkeypatch, capsys):

    # Set (http, _) to setup_http(monkeypatch, [{'status': 'PLACED'}, {'status':
    # 'PREPARING'}, {'status': 'DELIVERED'}]).
    http, _ = setup_http(monkeypatch, [{'status': 'PLACED'}, {'status': 'PREPARING'}, {'status': 'DELIVERED'}])

    # Verify that client.simulate(1, delay=0) == 1.
    assert client.simulate(1, delay=0) == 1

    # Verify that http.call_count == 3.
    assert http.call_count == 3

    # Verify that 'Expected PREPARING' in capsys.readouterr().out.
    assert 'Expected PREPARING' in capsys.readouterr().out


# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('failure', [HTTPError('url', 404, 'missing', {}, None),
                                    # Continue the
                                    # expression
                                    # above.
                                    HTTPError('url', 409, 'conflict', {}, None),

                                    # Continue the
                                    # expression
                                    # above.
                                    URLError('offline'), TimeoutError('timeout')])

# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('on_patch', [True, False])
# Define the test for request failure stops without retry.
def test_request_failure_stops_without_retry(monkeypatch, capsys, failure, on_patch):

    # Set responses to [{'status': 'PLACED'}, failure] if on_patch else [failure].
    responses = [{'status': 'PLACED'}, failure] if on_patch else [failure]

    # Set (http, _) to setup_http(monkeypatch, responses).
    http, _ = setup_http(monkeypatch, responses)

    # Verify that client.simulate(1, delay=0) == 1.
    assert client.simulate(1, delay=0) == 1

    # Verify that http.call_count == len(responses).
    assert http.call_count == len(responses)

    # Set output to capsys.readouterr().out.
    output = capsys.readouterr().out

    # Verify that 'API request failed' in output.
    assert 'API request failed' in output

    # Verify that 'Order 1: PREPARING' not in output.
    assert 'Order 1: PREPARING' not in output


# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('response', [{}, [], {'status': None}])
# Define the test for malformed response stops.
def test_malformed_response_stops(monkeypatch, response):

    # Set (http, _) to setup_http(monkeypatch, [response]).
    http, _ = setup_http(monkeypatch, [response])

    # Verify that client.simulate(1, delay=0) == 1.
    assert client.simulate(1, delay=0) == 1

    # Verify that http.call_count == 1.
    assert http.call_count == 1


# Define the test for patch must confirm transition.
def test_patch_must_confirm_transition(monkeypatch):

    # Set (http, _) to setup_http(monkeypatch, [{'status': 'PLACED'}, {'status':
    # 'PLACED'}]).
    http, _ = setup_http(monkeypatch, [{'status': 'PLACED'}, {'status': 'PLACED'}])

    # Verify that client.simulate(1, delay=0) == 1.
    assert client.simulate(1, delay=0) == 1

    # Verify that http.call_count == 2.
    assert http.call_count == 2


# Define the test for ctrl c stops.
def test_ctrl_c_stops(monkeypatch, capsys):

    # Set (http, sleep) to setup_http(monkeypatch, []).
    http, sleep = setup_http(monkeypatch, [])

    # Set sleep.side_effect to KeyboardInterrupt.
    sleep.side_effect = KeyboardInterrupt

    # Verify that client.simulate(1) == 130.
    assert client.simulate(1) == 130

    # Call http.assert_not_called().
    http.assert_not_called()

    # Verify that 'Simulation stopped' in capsys.readouterr().out.
    assert 'Simulation stopped' in capsys.readouterr().out


# Define the test for cli defaults and options.
def test_cli_defaults_and_options(monkeypatch):

    # Set simulate to Mock(return_value=0).
    simulate = Mock(return_value=0)

    # Call monkeypatch.setattr(client, 'simulate', simulate).
    monkeypatch.setattr(client, 'simulate', simulate)

    # Verify that client.main(['1']) == 0.
    assert client.main(['1']) == 0

    # Call simulate.assert_called_with(1, 'http://127.0.0.1:8000', 3).
    simulate.assert_called_with(1, 'http://127.0.0.1:8000', 3)

    # Call client.main(['2', '--base-url', 'http://example.test', '--delay', '0']).
    client.main(['2', '--base-url', 'http://example.test', '--delay', '0'])

    # Call simulate.assert_called_with(2, 'http://example.test', 0).
    simulate.assert_called_with(2, 'http://example.test', 0)


# Apply this decorator to configure the function defined below.
@pytest.mark.parametrize('args', [['0'], ['1', '--delay', '-1'], ['1', '--delay', 'nan'],
                                 # Continue the
                                 # expression above.
                                 ['1', '--delay', 'inf'], ['1', '--base-url', 'file:///tmp']])

# Define the test for invalid cli inputs.
def test_invalid_cli_inputs(args):

    # Enter pytest.raises(SystemExit) and run the indented block with its cleanup
    # behavior.
    with pytest.raises(SystemExit) as error:

        # Call client.main(args).
        client.main(args)

    # Verify that error.value.code == 2.
    assert error.value.code == 2

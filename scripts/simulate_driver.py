"""Drive an existing PLACED order through the demonstration lifecycle."""

# Import argparse for use in this module.
import argparse

# Import json for use in this module.
import json

# Import math for use in this module.
import math

# Import time for use in this module.
import time

# Import HTTPException from http.client.
from http.client import HTTPException

# Import HTTPError, URLError from urllib.error.
from urllib.error import HTTPError, URLError

# Import urlsplit from urllib.parse.
from urllib.parse import urlsplit

# Import Request, urlopen from urllib.request.
from urllib.request import Request, urlopen


# Set STATUSES to ('PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED').
STATUSES = ('PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED')


# Define request order.
def request_order(url, status=None):

    # Build the value below and store it in request.
    request = Request(url) if status is None else Request(

        # Supply the remaining arguments or values for the expression above.
        url + '/status', data=json.dumps({'status': status}).encode(),

        # Supply the remaining arguments or values for the expression above.
        headers={'Content-Type': 'application/json'}, method='PATCH')

    # Enter urlopen(request, timeout=10) and run the indented block with its cleanup
    # behavior.
    with urlopen(request, timeout=10) as response:

        # Set order to json.load(response).
        order = json.load(response)

    # Run this branch when not isinstance(order, dict) or not
    # isinstance(order.get('status'), str).
    if not isinstance(order, dict) or not isinstance(order.get('status'), str):

        # Raise ValueError('Invalid order response') to report the failure.
        raise ValueError('Invalid order response')

    # Return order.
    return order


# Define simulate.
def simulate(order_id, base_url='http://127.0.0.1:8000', delay=3):

    # Set url to f"{base_url.rstrip('/')}/orders/{order_id}".
    url = f'{base_url.rstrip("/")}/orders/{order_id}'

    # Attempt these operations and handle the exceptions listed below.
    try:

        # Loop over zip(STATUSES, STATUSES[1:]), assigning each value to (current,
        # target).
        for current, target in zip(STATUSES, STATUSES[1:]):
            # Recheck after waiting: another client may have changed the order.
            # Call time.sleep(delay).
            time.sleep(delay)

            # Set order to request_order(url).
            order = request_order(url)

            # Run this branch when order['status'] != current.
            if order['status'] != current:

                # Call print(f"Expected {current}, found
                # {order['status']}; simulation stopped.").
                print(f"Expected {current}, found {order['status']}; simulation stopped.")

                # Return 1.
                return 1

            # Set updated to request_order(url, target).
            updated = request_order(url, target)

            # Run this branch when updated['status'] != target.
            if updated['status'] != target:

                # Call print(f'API did not confirm {target}; simulation
                # stopped.').
                print(f'API did not confirm {target}; simulation stopped.')

                # Return 1.
                return 1

            # Call print(f'Order {order_id}: {target}', flush=True).
            print(f'Order {order_id}: {target}', flush=True)

        # Return 0.
        return 0
    # Handle HTTPError.
    except HTTPError as error:

        # Call print(f'API request failed: HTTP {error.code}; simulation
        # stopped.').
        print(f'API request failed: HTTP {error.code}; simulation stopped.')

        # Call error.close().
        error.close()

        # Return 1.
        return 1
    # Handle (URLError, OSError, HTTPException, ValueError).
    except (URLError, OSError, HTTPException, ValueError) as error:

        # Call print(f'API request failed: {error}; simulation stopped.').
        print(f'API request failed: {error}; simulation stopped.')

        # Return 1.
        return 1
    # Handle KeyboardInterrupt.
    except KeyboardInterrupt:

        # Call print('\nSimulation stopped.').
        print('\nSimulation stopped.')

        # Return 130.
        return 130


# Define main.
def main(argv=None):

    # Set parser to argparse.ArgumentParser(description='Simulate the full lifecycle
    # of a PLACED order.').
    parser = argparse.ArgumentParser(description='Simulate the full lifecycle of a PLACED order.')

    # Call parser.add_argument('order_id', type=int).
    parser.add_argument('order_id', type=int)

    # Call parser.add_argument('--base-url', default='http://127.0.0.1:8000').
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')

    # Call parser.add_argument('--delay', type=float, default=3, help='Seconds before
    # each transition (default: 3)').
    parser.add_argument('--delay', type=float, default=3, help='Seconds before each transition (default: 3)')

    # Set args to parser.parse_args(argv).
    args = parser.parse_args(argv)

    # Run this branch when args.order_id <= 0.
    if args.order_id <= 0:

        # Call parser.error('order_id must be positive').
        parser.error('order_id must be positive')

    # Run this branch when not math.isfinite(args.delay) or args.delay < 0.
    if not math.isfinite(args.delay) or args.delay < 0:

        # Call parser.error('delay must be finite and nonnegative').
        parser.error('delay must be finite and nonnegative')

    # Set parsed to urlsplit(args.base_url).
    parsed = urlsplit(args.base_url)

    # Run this branch when parsed.scheme not in ('http', 'https') or not parsed.netloc
    # or parsed.query or parsed.fragment.
    if parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.query or parsed.fragment:

        # Call parser.error('base URL must be an HTTP(S) URL without a query or
        # fragment').
        parser.error('base URL must be an HTTP(S) URL without a query or fragment')

    # Return simulate(args.order_id, args.base_url, args.delay).
    return simulate(args.order_id, args.base_url, args.delay)


# Run this branch when __name__ == '__main__'.
if __name__ == '__main__':

    # Raise SystemExit(main()) to report the failure.
    raise SystemExit(main())

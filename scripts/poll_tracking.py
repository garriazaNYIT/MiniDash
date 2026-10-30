"""Poll order tracking: python scripts/poll_tracking.py 1 --base-url http://localhost:8000"""

# Import argparse for use in this module.
import argparse

# Import json for use in this module.
import json

# Import time for use in this module.
import time

# Import HTTPError, URLError from urllib.error.
from urllib.error import HTTPError, URLError

# Import urlsplit from urllib.parse.
from urllib.parse import urlsplit

# Import urlopen from urllib.request.
from urllib.request import urlopen


# Define poll.
def poll(order_id, base_url='http://127.0.0.1:8000'):
    """Display changed snapshots; retry network/5xx failures until interrupted."""

    # Set url to f"{base_url.rstrip('/')}/orders/{order_id}/tracking".
    url = f'{base_url.rstrip("/")}/orders/{order_id}/tracking'

    # Set previous to None.
    previous = None

    # Attempt these operations and handle the exceptions listed below.
    try:

        # Repeat while True.
        while True:

            # Attempt these operations and handle the exceptions listed below.
            try:

                # Enter urlopen(url, timeout=10) and run the indented
                # block with its cleanup behavior.
                with urlopen(url, timeout=10) as response:

                    # Set tracking to json.load(response).
                    tracking = json.load(response)

                # Run this branch when not isinstance(tracking, dict) or
                # not all((key in tracking for key in ('status',
                # 'estimated_delivery_at', 'remaining_minutes'))).
                if not isinstance(tracking, dict) or not all(

                    # Supply the remaining arguments or values for the
                    # expression above.
                    key in tracking for key in ('status', 'estimated_delivery_at', 'remaining_minutes')

                # Finish the expression started above.
                ):

                    # Raise ValueError('missing tracking fields') to
                    # report the failure.
                    raise ValueError('missing tracking fields')
            # Handle HTTPError.
            except HTTPError as error:

                # Set code to error.code.
                code = error.code

                # Call error.close().
                error.close()

                # Run this branch when code == 404.
                if code == 404:

                    # Call print(f'Order {order_id} not found.').
                    print(f'Order {order_id} not found.')

                    # Return 1.
                    return 1

                # Run this branch when code < 500.
                if code < 500:

                    # Call print(f'Tracking request failed: HTTP
                    # {code}.').
                    print(f'Tracking request failed: HTTP {code}.')

                    # Return 1.
                    return 1

                # Call print(f'Temporary server failure (HTTP {code});
                # retrying in 2 seconds.', flush=True).
                print(f'Temporary server failure (HTTP {code}); retrying in 2 seconds.', flush=True)
            # Handle (URLError, TimeoutError, ConnectionError, OSError).
            except (URLError, TimeoutError, ConnectionError, OSError) as error:

                # Call print(f'Connection failed: {error}. Retrying in 2
                # seconds.', flush=True).
                print(f'Connection failed: {error}. Retrying in 2 seconds.', flush=True)
            # Handle (ValueError, UnicodeError).
            except (ValueError, UnicodeError):

                # Call print('Invalid tracking response; stopping.').
                print('Invalid tracking response; stopping.')

                # Return 1.
                return 1
            # Handle the alternative case or the successful try-block result.
            else:

                # Run this branch when tracking != previous.
                if tracking != previous:

                    # Call print(f"Status: {tracking['status']} | ETA:
                    # {tracking['estimated_delivery_at']} | Remaining
                    # minutes: {tracking['remaining_minutes']}",
                    # flush=True).
                    print(f"Status: {tracking['status']} | ETA: {tracking['estimated_delivery_at']}"

                          # Supply the remaining arguments or
                          # values for the expression above.
                          f" | Remaining minutes: {tracking['remaining_minutes']}", flush=True)

                    # Set previous to tracking.
                    previous = tracking

                # Run this branch when tracking['status'] in ('DELIVERED',
                # 'CANCELLED').
                if tracking['status'] in ('DELIVERED', 'CANCELLED'):

                    # Return 0.
                    return 0

            # Call time.sleep(2).
            time.sleep(2)
    # Handle KeyboardInterrupt.
    except KeyboardInterrupt:

        # Call print('\nPolling stopped.').
        print('\nPolling stopped.')

        # Return 0.
        return 0


# Define main.
def main(argv=None):

    # Set parser to argparse.ArgumentParser(description='Poll live order tracking
    # every two seconds.').
    parser = argparse.ArgumentParser(description='Poll live order tracking every two seconds.')

    # Call parser.add_argument('order_id', type=int).
    parser.add_argument('order_id', type=int)

    # Call parser.add_argument('--base-url', default='http://127.0.0.1:8000').
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')

    # Set args to parser.parse_args(argv).
    args = parser.parse_args(argv)

    # Run this branch when args.order_id <= 0.
    if args.order_id <= 0:

        # Call parser.error('order_id must be positive').
        parser.error('order_id must be positive')

    # Set parsed to urlsplit(args.base_url).
    parsed = urlsplit(args.base_url)

    # Run this branch when parsed.scheme not in ('http', 'https') or not parsed.netloc
    # or parsed.query or parsed.fragment.
    if parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.query or parsed.fragment:

        # Call parser.error('base URL must be an HTTP(S) URL without a query or
        # fragment').
        parser.error('base URL must be an HTTP(S) URL without a query or fragment')

    # Return poll(args.order_id, args.base_url).
    return poll(args.order_id, args.base_url)


# Run this branch when __name__ == '__main__'.
if __name__ == '__main__':

    # Raise SystemExit(main()) to report the failure.
    raise SystemExit(main())

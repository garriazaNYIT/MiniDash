"""Poll order tracking: python scripts/poll_tracking.py 1 --base-url http://localhost:8000"""
import argparse
import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import urlopen


def poll(order_id, base_url='http://127.0.0.1:8000'):
    """Display changed snapshots; retry network/5xx failures until interrupted."""
    url = f'{base_url.rstrip("/")}/orders/{order_id}/tracking'
    previous = None
    try:
        while True:
            try:
                with urlopen(url, timeout=10) as response:
                    tracking = json.load(response)
                if not isinstance(tracking, dict) or not all(
                    key in tracking for key in ('status', 'estimated_delivery_at', 'remaining_minutes')
                ):
                    raise ValueError('missing tracking fields')
            except HTTPError as error:
                code = error.code
                error.close()
                if code == 404:
                    print(f'Order {order_id} not found.')
                    return 1
                if code < 500:
                    print(f'Tracking request failed: HTTP {code}.')
                    return 1
                print(f'Temporary server failure (HTTP {code}); retrying in 2 seconds.', flush=True)
            except (URLError, TimeoutError, ConnectionError, OSError) as error:
                print(f'Connection failed: {error}. Retrying in 2 seconds.', flush=True)
            except (ValueError, UnicodeError):
                print('Invalid tracking response; stopping.')
                return 1
            else:
                if tracking != previous:
                    print(f"Status: {tracking['status']} | ETA: {tracking['estimated_delivery_at']}"
                          f" | Remaining minutes: {tracking['remaining_minutes']}", flush=True)
                    previous = tracking
                if tracking['status'] in ('DELIVERED', 'CANCELLED'):
                    return 0
            time.sleep(2)
    except KeyboardInterrupt:
        print('\nPolling stopped.')
        return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description='Poll live order tracking every two seconds.')
    parser.add_argument('order_id', type=int)
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    args = parser.parse_args(argv)
    if args.order_id <= 0:
        parser.error('order_id must be positive')
    parsed = urlsplit(args.base_url)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.query or parsed.fragment:
        parser.error('base URL must be an HTTP(S) URL without a query or fragment')
    return poll(args.order_id, args.base_url)


if __name__ == '__main__':
    raise SystemExit(main())

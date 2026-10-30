"""Drive an existing PLACED order through the demonstration lifecycle."""
import argparse
import json
import math
import time
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


STATUSES = ('PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED')


def request_order(url, status=None):
    request = Request(url) if status is None else Request(
        url + '/status', data=json.dumps({'status': status}).encode(),
        headers={'Content-Type': 'application/json'}, method='PATCH')
    with urlopen(request, timeout=10) as response:
        order = json.load(response)
    if not isinstance(order, dict) or not isinstance(order.get('status'), str):
        raise ValueError('Invalid order response')
    return order


def simulate(order_id, base_url='http://127.0.0.1:8000', delay=3):
    url = f'{base_url.rstrip("/")}/orders/{order_id}'
    try:
        for current, target in zip(STATUSES, STATUSES[1:]):
            # Recheck after waiting: another client may have changed the order.
            time.sleep(delay)
            order = request_order(url)
            if order['status'] != current:
                print(f"Expected {current}, found {order['status']}; simulation stopped.")
                return 1
            updated = request_order(url, target)
            if updated['status'] != target:
                print(f'API did not confirm {target}; simulation stopped.')
                return 1
            print(f'Order {order_id}: {target}', flush=True)
        return 0
    except HTTPError as error:
        print(f'API request failed: HTTP {error.code}; simulation stopped.')
        error.close()
        return 1
    except (URLError, OSError, HTTPException, ValueError) as error:
        print(f'API request failed: {error}; simulation stopped.')
        return 1
    except KeyboardInterrupt:
        print('\nSimulation stopped.')
        return 130


def main(argv=None):
    parser = argparse.ArgumentParser(description='Simulate the full lifecycle of a PLACED order.')
    parser.add_argument('order_id', type=int)
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--delay', type=float, default=3, help='Seconds before each transition (default: 3)')
    args = parser.parse_args(argv)
    if args.order_id <= 0:
        parser.error('order_id must be positive')
    if not math.isfinite(args.delay) or args.delay < 0:
        parser.error('delay must be finite and nonnegative')
    parsed = urlsplit(args.base_url)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.query or parsed.fragment:
        parser.error('base URL must be an HTTP(S) URL without a query or fragment')
    return simulate(args.order_id, args.base_url, args.delay)


if __name__ == '__main__':
    raise SystemExit(main())

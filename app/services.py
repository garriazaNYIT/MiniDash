"""Business rules and atomic order operations."""
from datetime import datetime, timezone

from fastapi import HTTPException

from .order_tracking import is_status_change
from .eta import estimate_delivery, remaining_minutes

class OrderService:
    def __init__(self, repository):
        self.repository = repository

    def create(self, payload):
        address = payload.address.strip()
        if not address:
            raise HTTPException(422, 'Address must not be blank')
        repo = self.repository
        with repo.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            restaurant = repo.restaurant(db, payload.restaurant_id)
            if not restaurant:
                raise HTTPException(404, 'Restaurant not found')
            items = []
            seen = set()
            for requested in payload.items:
                if requested.menu_item_id in seen:
                    raise HTTPException(422, 'Duplicate menu item; use quantity instead')
                seen.add(requested.menu_item_id)
                item = repo.menu_item(db, requested.menu_item_id)
                if item is None or item['restaurant_id'] != payload.restaurant_id:
                    raise HTTPException(422, 'Menu item does not belong to this restaurant')
                items.append((item['id'], requested.quantity, item['price_cents']))
            total = sum(quantity * price for _, quantity, price in items)
            if total > 9223372036854775807:
                raise HTTPException(422, 'Order total exceeds supported range')
            now = datetime.now(timezone.utc)
            try:
                estimate = estimate_delivery('PLACED', now.isoformat(),
                                             restaurant['avg_prep_minutes'], payload.delivery_distance_km, now)
            except OverflowError:
                raise HTTPException(422, 'Delivery estimate exceeds supported date range') from None
            order_id = repo.insert_order(db, payload.restaurant_id, total, address,
                                         now.isoformat(), items, payload.delivery_distance_km)
            repo.update_eta(db, order_id, estimate, now.isoformat())
            return repo.order(db, order_id)

    def get(self, order_id):
        with self.repository.connect() as db:
            order = self.repository.order(db, order_id)
            if order is None:
                raise HTTPException(404, 'Order not found')
            return order

    def tracking(self, order_id):
        repo = self.repository
        with repo.connect() as db:
            # Keep the order and history reads in the same SQLite snapshot.
            db.execute('BEGIN')
            order = repo.order(db, order_id)
            if order is None:
                raise HTTPException(404, 'Order not found')
            return {
                'order_id': order['id'],
                'status': order['status'],
                'history': repo.status_history(db, order_id),
                'estimated_delivery_at': order['estimated_delivery_at'],
                'eta_updated_at': order['eta_updated_at'],
                'remaining_minutes': 0 if order['status'] == 'DELIVERED' else remaining_minutes(
                    order['estimated_delivery_at'], datetime.now(timezone.utc)),
            }

    def change_status(self, order_id, status):
        repo = self.repository
        with repo.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            order = repo.order(db, order_id)
            if order is None:
                raise HTTPException(404, 'Order not found')
            try:
                changed = is_status_change(order['status'], status)
            except ValueError:
                raise HTTPException(409, 'Invalid status transition') from None
            if not changed:
                return order
            now = datetime.now(timezone.utc)
            restaurant = repo.restaurant(db, order['restaurant_id'])
            estimate = estimate_delivery(status, order['created_at'], restaurant['avg_prep_minutes'],
                                         order['delivery_distance_km'], now)
            repo.update_status(db, order_id, status)
            repo.append_status_history(db, order_id, status, now.isoformat())
            repo.update_eta(db, order_id, estimate, now.isoformat())
            return repo.order(db, order_id)

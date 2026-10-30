"""Business rules and atomic order operations."""

# Import datetime, timezone from datetime.
from datetime import datetime, timezone

# Import HTTPException from fastapi.
from fastapi import HTTPException

# Import is_status_change from .order_tracking.
from .order_tracking import is_status_change

# Import estimate_delivery, remaining_minutes from .eta.
from .eta import estimate_delivery, remaining_minutes

# Define the OrderService class.
class OrderService:

    # Initialize the object with its required collaborators.
    def __init__(self, repository):

        # Set self.repository to repository.
        self.repository = repository

    # Define create.
    def create(self, payload):

        # Set address to payload.address.strip().
        address = payload.address.strip()

        # Run this branch when not address.
        if not address:

            # Raise HTTPException(422, 'Address must not be blank') to report
            # the failure.
            raise HTTPException(422, 'Address must not be blank')

        # Set repo to self.repository.
        repo = self.repository

        # Enter repo.connect() and run the indented block with its cleanup
        # behavior.
        with repo.connect() as db:

            # Call db.execute('BEGIN IMMEDIATE').
            db.execute('BEGIN IMMEDIATE')

            # Set restaurant to repo.restaurant(db, payload.restaurant_id).
            restaurant = repo.restaurant(db, payload.restaurant_id)

            # Run this branch when not restaurant.
            if not restaurant:

                # Raise HTTPException(404, 'Restaurant not found') to
                # report the failure.
                raise HTTPException(404, 'Restaurant not found')

            # Set items to [].
            items = []

            # Set seen to set().
            seen = set()

            # Loop over payload.items, assigning each value to requested.
            for requested in payload.items:

                # Run this branch when requested.menu_item_id in seen.
                if requested.menu_item_id in seen:

                    # Raise HTTPException(422, 'Duplicate menu item;
                    # use quantity instead') to report the failure.
                    raise HTTPException(422, 'Duplicate menu item; use quantity instead')

                # Call seen.add(requested.menu_item_id).
                seen.add(requested.menu_item_id)

                # Set item to repo.menu_item(db, requested.menu_item_id).
                item = repo.menu_item(db, requested.menu_item_id)

                # Run this branch when item is None or
                # item['restaurant_id'] != payload.restaurant_id.
                if item is None or item['restaurant_id'] != payload.restaurant_id:

                    # Raise HTTPException(422, 'Menu item does not
                    # belong to this restaurant') to report the
                    # failure.
                    raise HTTPException(422, 'Menu item does not belong to this restaurant')

                # Call items.append((item['id'], requested.quantity,
                # item['price_cents'])).
                items.append((item['id'], requested.quantity, item['price_cents']))

            # Set total to sum((quantity * price for _, quantity, price in
            # items)).
            total = sum(quantity * price for _, quantity, price in items)

            # Run this branch when total > 9223372036854775807.
            if total > 9223372036854775807:

                # Raise HTTPException(422, 'Order total exceeds supported
                # range') to report the failure.
                raise HTTPException(422, 'Order total exceeds supported range')

            # Set now to datetime.now(timezone.utc).
            now = datetime.now(timezone.utc)

            # Attempt these operations and handle the exceptions listed below.
            try:

                # Set estimate to estimate_delivery('PLACED',
                # now.isoformat(), restaurant['avg_prep_minutes'],
                # payload.delivery_distance_km, now).
                estimate = estimate_delivery('PLACED', now.isoformat(),

                                             # Supply
                                             # the
                                             # remaining
                                             # arguments
                                             # or
                                             # values
                                             # for
                                             # the
                                             # expression
                                             # above.
                                             restaurant['avg_prep_minutes'], payload.delivery_distance_km, now)
            # Handle OverflowError.
            except OverflowError:

                # Raise HTTPException(422, 'Delivery estimate exceeds
                # supported date range') to report the failure.
                raise HTTPException(422, 'Delivery estimate exceeds supported date range') from None

            # Build the value below and store it in order_id.
            order_id = repo.insert_order(db, payload.restaurant_id, total, address,

                                         # Supply
                                         # the
                                         # remaining
                                         # arguments
                                         # or
                                         # values
                                         # for
                                         # the
                                         # expression
                                         # above.
                                         now.isoformat(), items, payload.delivery_distance_km)

            # Call repo.update_eta(db, order_id, estimate, now.isoformat()).
            repo.update_eta(db, order_id, estimate, now.isoformat())

            # Return repo.order(db, order_id).
            return repo.order(db, order_id)

    # Define get.
    def get(self, order_id):

        # Enter self.repository.connect() and run the indented block with its
        # cleanup behavior.
        with self.repository.connect() as db:

            # Set order to self.repository.order(db, order_id).
            order = self.repository.order(db, order_id)

            # Run this branch when order is None.
            if order is None:

                # Raise HTTPException(404, 'Order not found') to report
                # the failure.
                raise HTTPException(404, 'Order not found')

            # Return order.
            return order

    # Define tracking.
    def tracking(self, order_id):

        # Set repo to self.repository.
        repo = self.repository

        # Enter repo.connect() and run the indented block with its cleanup
        # behavior.
        with repo.connect() as db:
            # Keep the order and history reads in the same SQLite snapshot.
            # Call db.execute('BEGIN').
            db.execute('BEGIN')

            # Set order to repo.order(db, order_id).
            order = repo.order(db, order_id)

            # Run this branch when order is None.
            if order is None:

                # Raise HTTPException(404, 'Order not found') to report
                # the failure.
                raise HTTPException(404, 'Order not found')

            # Build and return the response fields below.
            return {

                # Identify the order being tracked.
                'order_id': order['id'],

                # Include the current order status.
                'status': order['status'],

                # Include the ordered status events from SQLite.
                'history': repo.status_history(db, order_id),

                # Include the stored delivery estimate.
                'estimated_delivery_at': order['estimated_delivery_at'],

                # Include when the estimate was last updated.
                'eta_updated_at': order['eta_updated_at'],

                # Calculate remaining minutes without updating storage.
                'remaining_minutes': 0 if order['status'] == 'DELIVERED' else remaining_minutes(

                    # Supply the remaining arguments or values for the
                    # expression above.
                    order['estimated_delivery_at'], datetime.now(timezone.utc)),

            # Finish the expression started above.
            }

    # Define change status.
    def change_status(self, order_id, status):

        # Set repo to self.repository.
        repo = self.repository

        # Enter repo.connect() and run the indented block with its cleanup
        # behavior.
        with repo.connect() as db:

            # Call db.execute('BEGIN IMMEDIATE').
            db.execute('BEGIN IMMEDIATE')

            # Set order to repo.order(db, order_id).
            order = repo.order(db, order_id)

            # Run this branch when order is None.
            if order is None:

                # Raise HTTPException(404, 'Order not found') to report
                # the failure.
                raise HTTPException(404, 'Order not found')

            # Attempt these operations and handle the exceptions listed below.
            try:

                # Set changed to is_status_change(order['status'],
                # status).
                changed = is_status_change(order['status'], status)
            # Handle ValueError.
            except ValueError:

                # Raise HTTPException(409, 'Invalid status transition') to
                # report the failure.
                raise HTTPException(409, 'Invalid status transition') from None

            # Run this branch when not changed.
            if not changed:

                # Return order.
                return order

            # Set now to datetime.now(timezone.utc).
            now = datetime.now(timezone.utc)

            # Set restaurant to repo.restaurant(db, order['restaurant_id']).
            restaurant = repo.restaurant(db, order['restaurant_id'])

            # Build the value below and store it in estimate.
            estimate = estimate_delivery(status, order['created_at'], restaurant['avg_prep_minutes'],

                                         # Supply
                                         # the
                                         # remaining
                                         # arguments
                                         # or
                                         # values
                                         # for
                                         # the
                                         # expression
                                         # above.
                                         order['delivery_distance_km'], now)

            # Call repo.update_status(db, order_id, status).
            repo.update_status(db, order_id, status)

            # Call repo.append_status_history(db, order_id, status,
            # now.isoformat()).
            repo.append_status_history(db, order_id, status, now.isoformat())

            # Call repo.update_eta(db, order_id, estimate, now.isoformat()).
            repo.update_eta(db, order_id, estimate, now.isoformat())

            # Return repo.order(db, order_id).
            return repo.order(db, order_id)

# services.py

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import Cart, Order, OrderItem


class OrderService:

    @staticmethod
    @transaction.atomic
    def create_from_cart(user):
        # One query — evaluate into memory immediately
        cart_items = list(Cart.objects.filter(user=user))

        if not cart_items:
            raise ValidationError("Cannot create order from empty cart.")

        # Python sum — cart_items already in memory, no extra query
        total = sum(item.price for item in cart_items)

        # Direct creation — no serializer, pure business logic
        order = Order.objects.create(
            user=user,
            total=total,
            status=False
        )

        # Bulk create — one query for all items
        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                menuitem=item.menuitem,
                quantity=item.quantity,
                unit_price=item.unit_price,
                price=item.price
            )
            for item in cart_items  # iterates in-memory list
        ])

        # Clear cart
        Cart.objects.filter(user=user).delete()

        return order
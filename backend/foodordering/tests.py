from django.test import TestCase
from django.urls import reverse

from .models import User, Category, Food, Order


class UpdateCartQuantityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            first_name="Test", last_name="User", email="test@example.com", mobile="9999999999"
        )
        self.category = Category.objects.create(category_name="Snacks")
        self.food = Food.objects.create(
            category=self.category, item_name="Fries", price="99.00",
            item_quantity="1 plate", image="food_images/vegBurger.png",
        )
        self.order = Order.objects.create(user=self.user, food=self.food, quantity=1, is_order_placed=False)

    def test_valid_quantity_updates(self):
        response = self.client.put(
            reverse("update_cart_quantity"),
            data={"orderId": self.order.id, "quantity": 5},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.quantity, 5)

    def test_zero_quantity_is_rejected(self):
        response = self.client.put(
            reverse("update_cart_quantity"),
            data={"orderId": self.order.id, "quantity": 0},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.quantity, 1)

    def test_negative_quantity_is_rejected(self):
        response = self.client.put(
            reverse("update_cart_quantity"),
            data={"orderId": self.order.id, "quantity": -3},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.quantity, 1)

    def test_non_numeric_quantity_is_rejected(self):
        response = self.client.put(
            reverse("update_cart_quantity"),
            data={"orderId": self.order.id, "quantity": "abc"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.quantity, 1)

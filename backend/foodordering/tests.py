from django.test import TestCase
from django.urls import reverse

from .models import User, Category, Food, Order, Review


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


class AddReviewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            first_name="Test", last_name="User", email="review@example.com", mobile="8888888888"
        )
        self.category = Category.objects.create(category_name="Snacks")
        self.food = Food.objects.create(
            category=self.category, item_name="Fries", price="99.00",
            item_quantity="1 plate", image="food_images/vegBurger.png",
        )

    def test_valid_rating_is_accepted(self):
        response = self.client.post(
            reverse("add_review", args=[self.food.id]),
            data={"user_id": self.user.id, "rating": 4, "comment": "Good"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(Review.objects.first().rating, 4)

    def test_rating_above_five_is_rejected(self):
        response = self.client.post(
            reverse("add_review", args=[self.food.id]),
            data={"user_id": self.user.id, "rating": 999, "comment": "Too many stars"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Review.objects.count(), 0)

    def test_rating_below_one_is_rejected(self):
        response = self.client.post(
            reverse("add_review", args=[self.food.id]),
            data={"user_id": self.user.id, "rating": 0, "comment": "No stars"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Review.objects.count(), 0)

    def test_non_numeric_rating_is_rejected(self):
        response = self.client.post(
            reverse("add_review", args=[self.food.id]),
            data={"user_id": self.user.id, "rating": "great", "comment": "Not a number"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Review.objects.count(), 0)


class ReviewsDetailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            first_name="Test", last_name="User", email="edit@example.com", mobile="7777777777"
        )
        self.category = Category.objects.create(category_name="Snacks")
        self.food = Food.objects.create(
            category=self.category, item_name="Fries", price="99.00",
            item_quantity="1 plate", image="food_images/vegBurger.png",
        )
        self.review = Review.objects.create(user=self.user, food=self.food, rating=3, comment="Ok")

    def test_updating_rating_above_five_is_rejected(self):
        response = self.client.put(
            reverse("reviews_detail", args=[self.review.id]),
            data={"rating": 999},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 3)

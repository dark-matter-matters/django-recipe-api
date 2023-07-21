"""
Tests for the ingredients API
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer

INGREDIENTS_URLS = reverse("recipe:ingredient-list")


def create_user(email="user@example.com", password="test123"):
    return get_user_model().objects.create(email=email, password=password)


def detail_url(ingredient_id):
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


class PublicIngerdientsApiTests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(INGREDIENTS_URLS)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientTests(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        Ingredient.objects.create(user=self.user, name="Kale")
        Ingredient.objects.create(user=self.user, name="Vanilla")

        res = self.client.get(INGREDIENTS_URLS)

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        user2 = create_user("user2@example.com")
        Ingredient.objects.create(user=user2, name="SAlt")
        ingredient = Ingredient.objects.create(user=self.user, name="Pepper")

        res = self.client.get(INGREDIENTS_URLS)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], ingredient.name)
        self.assertEqual(res.data[0]["id"], ingredient.id)

    def test_update_ingredient(self):
        ingredient = Ingredient.objects.create(user=self.user, name="Cilantro")

        payload = {"name": "Coriander"}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredient(self):
        ingredient = Ingredient.objects.create(user=self.user, name="Lettuce")

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        in1 = Ingredient.objects.create(user=self.user, name="Apples")
        in2 = Ingredient.objects.create(user=self.user, name="Turkey")
        recipe = Recipe.objects.create(
            user=self.user, title="Apple crumble", time_minutes=5, price=Decimal("4.4")
        )

        recipe.ingredients.add(in1)

        res = self.client.get(INGREDIENTS_URLS, {"assigned_only": 1})

        s1 = IngredientSerializer(in1)
        s2 = IngredientSerializer(in2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_ngredients_unique(self):
        ing = Ingredient.objects.create(user=self.user, name="Eggs")
        Ingredient.objects.create(user=self.user, name="Lentils")
        recipe1 = Recipe.objects.create(
            user=self.user, title="Eggs benedict", time_minutes=3, price=Decimal("4.4")
        )
        recipe2 = Recipe.objects.create(
            user=self.user, title="Herb egg", time_minutes=22, price=Decimal("4.4")
        )
        recipe1.ingredients.add(ing)
        recipe2.ingredients.add(ing)

        res = self.client.get(INGREDIENTS_URLS, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)

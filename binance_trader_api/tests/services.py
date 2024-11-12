from django.test import TestCase
from binance_trader_api.models import User
from binance_trader_api.services import UserService

class TestCreateUserServiceTestCase(TestCase):
    """Test case for User creation."""

    def setUp(self):
        self.user_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
        }

    def test_create_user(self):
        """Test the create_user function."""
        user_created = UserService.create_user(self.user_data)
        self.assertIsInstance(user_created, User)
        self.assertEqual(user_created.name, self.user_data['name'])
        self.assertEqual(user_created.email, self.user_data['email'])

class TestGetUserServiceTestCase(TestCase):
    """Test case for User retrieval."""

    def setUp(self):
        self.user_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
        }

    def test_get_user(self):
        """Test the get_user function."""
        user_created = UserService.create_user(self.user_data)
        self.user_data['user_token'] = user_created.user_token

        retrieved_user = UserService.get_user(self.user_data)
        self.assertIsInstance(retrieved_user, User)
        self.assertEqual(retrieved_user.name, self.user_data['name'])
        self.assertEqual(retrieved_user.email, self.user_data['email'])
        self.assertEqual(retrieved_user.user_token, self.user_data['user_token'])

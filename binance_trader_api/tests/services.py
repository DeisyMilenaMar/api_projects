from django.test import TestCase

from django.core.exceptions import ValidationError
from django.utils import timezone

from binance_trader_api.models import User
from binance_trader_api.models import Transaction

from binance_trader_api.factories import UserFactory
from binance_trader_api.factories import TransactionFactory

from binance_trader_api.services import UserService
from binance_trader_api.services import TransactionService


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


class TestTransactionServiceTestCase(TestCase):
    """Test case for Transaction creation."""
    def setUp(self):
        self.user = UserFactory()
        self.transaction_data = {
            'user_token':self.user.user_token,
            'buy_price':100.0,
            'buy_date': timezone.now(),
            'target_profit_percent': 0.15,
            'status': 'created'
        }
    def test_create_transaction_success(self):
        created_transaction = TransactionService.create_transaction(self.transaction_data)
        self.assertIsInstance(created_transaction, Transaction)
        self.assertEqual(created_transaction.user, self.user)
        self.assertEqual(created_transaction.buy_price, self.transaction_data['buy_price'])
        self.assertEqual(created_transaction.buy_date, self.transaction_data['buy_date'])
        self.assertEqual(created_transaction.target_profit_percent, self.transaction_data['target_profit_percent'])
        self.assertEqual(created_transaction.status, self.transaction_data['status'])

    def test_create_transaction_user_not_found(self):
        """Test creating a transaction with a non-existent user token."""
        self.transaction_data['user_token'] = 'nonexistent_token'

        with self.assertRaises(ValidationError) as context:
            TransactionService.create_transaction(self.transaction_data)
        
        self.assertEqual(str(context.exception), "['User with the provided token does not exist.']")

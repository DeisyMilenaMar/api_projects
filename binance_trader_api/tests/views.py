from datetime import datetime
from decimal import Decimal
from unittest.mock import patch
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError

from rest_framework.test import APITestCase
from binance_trader_api.factories import UserFactory, TransactionFactory
from binance_trader_api.models import Transaction, User
from binance_trader_api.services import TransactionService


class TransactionCreateViewTests(APITestCase):
    """Test suite for TransactionCreateView."""

    def setUp(self):
        """Set up the necessary data for the tests."""
        self.user = UserFactory()
        self.valid_transaction_data = {
            'user_token': self.user.user_token,
            'buy_price': Decimal('100.0'),
            'buy_date': timezone.now(),
            'target_profit_percent': Decimal('0.15'),
            'usdt_amount_buy':Decimal('10'),
            'status': 'created',
        }
        self.url = reverse('binance_trader_api:transactions_create')

    def test_create_transaction_success(self):
        """Test successful transaction creation."""
        response = self.client.post(
            self.url,
            data=self.valid_transaction_data,
            format='json'
        )
        json_response = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(json_response['buy_price']), self.valid_transaction_data['buy_price'])
        self.assertEqual(Decimal(json_response['usdt_amount_buy']), self.valid_transaction_data['usdt_amount_buy'])
        self.assertEqual(Decimal(json_response['target_profit_percent']), self.valid_transaction_data['target_profit_percent'])
        self.assertEqual(json_response['status'], self.valid_transaction_data['status'])      
        self.assertEqual(Transaction.objects.count(), 1)
        
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.buy_price, self.valid_transaction_data['buy_price'])
        self.assertEqual((transaction.usdt_amount_buy), self.valid_transaction_data['usdt_amount_buy'])
        self.assertEqual((transaction.target_profit_percent), self.valid_transaction_data['target_profit_percent'])
        self.assertEqual(transaction.status, self.valid_transaction_data['status'])

    def test_create_transaction_invalid_user_token(self):
        """Test transaction creation with invalid user token."""
        invalid_data = self.valid_transaction_data.copy()
        invalid_data['user_token'] = 'nonexistent_token'

        response = self.client.post(
            self.url,
            data=invalid_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Transaction.objects.count(), 0)
        self.assertIn('User with the provided token does not exist', str(response.data))

    def test_create_transaction_missing_required_fields(self):
        """Test transaction creation with missing required fields."""
        invalid_data = {
            'user_token': self.user.user_token,
            'buy_price': '100.00'  # Missing other required fields
        }

        response = self.client.post(
            self.url,
            data=invalid_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_create_transaction_invalid_values(self):
        """Test transaction creation with invalid field values."""
        invalid_data = self.valid_transaction_data.copy()
        invalid_data['buy_price'] = '-100.00'
        invalid_data['target_profit_percent'] = '2.0'

        response = self.client.post(
            self.url,
            data=invalid_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Transaction.objects.count(), 0)

    @patch('binance_trader_api.services.TransactionService.create_transaction')
    def test_service_error_handling(self, mock_create_transaction):
        """Test error handling when service raises an exception."""
        mock_create_transaction.side_effect = ValidationError('Service error')

        response = self.client.post(
            self.url,
            data=self.valid_transaction_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Transaction.objects.count(), 0)
        self.assertIn('Service error', str(response.data))


class UserCreateViewTest(APITestCase):
    """Test cases for UserCreateView."""
    def setUp(self):
        self.valid_payload = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
        }
        self.url = reverse('binance_trader_api:user-create')

    def test_create_user_success(self):
        """Test successful user creation."""
        response = self.client.post(
            self.url,
            self.valid_payload,
            format='json'
        )

        json_response = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json_response['name'], self.valid_payload['name'])
        self.assertEqual(json_response['email'], self.valid_payload['email'])
        self.assertIn('user_token', response.data)
        
        self.assertTrue(
            User.objects.filter(email=self.valid_payload['email']).exists()
        )

    def test_create_user_invalid_email(self):
        """Test user creation with invalid email."""
        invalid_payload = {
            'name': 'John Doe',
            'email': 'invalid-email'
        }

        response = self.client.post(
            self.url,
            invalid_payload,
            format='json'
        )
        json_response = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', json_response)
        self.assertIn('Enter a valid email address', json_response['error'])

    def test_create_user_missing_required_fields(self):
        """Test user creation with missing required fields."""
        incomplete_payload = {'name': 'John Doe'}
        response = self.client.post(self.url, incomplete_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_content = response.json().get('error', {})
        self.assertIn('email', error_content)
        self.assertIn('This field is required.', str(error_content))

    
class UserGetViewTest(APITestCase):
    """Test cases for UserGetView."""

    def setUp(self):
        """Set up test data."""
        User.objects.all().delete() 
        self.user = UserFactory()
        self.url = reverse('binance_trader_api:user-get')
        self.valid_params = {
            'name': self.user.name, 
            'email': self.user.email,
            'user_token': self.user.user_token
        }

    def test_get_user_success(self):
        """Test successful user retrieval."""
        response = self.client.get(self.url, self.valid_params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()

        self.assertEqual(json_response['name'], self.user.name)
        self.assertEqual(json_response['email'], self.user.email)
        self.assertEqual(json_response['user_token'], self.user.user_token)

    def test_get_user_not_found(self):
        """Test user retrieval with non-existent user."""
        invalid_params = {
            'name': 'Nonexistent User',
            'email': 'nonexistent@example.com',
            'user_token': 'invalid-token'
        }

        response = self.client.get(self.url, invalid_params)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'The response content must be rendered before it can be iterated over.')


    @patch('binance_trader_api.views.logger') 
    def test_get_user_logging_on_not_found(self, mock_logger):
        """Test that proper logging occurs when user is not found."""
        invalid_params = {
            'name': 'Nonexistent User',
            'email': 'nonexistent@example.com',
            'user_token': 'invalid-token'
        }
        response = self.client.get(self.url, invalid_params)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_logger.warning.assert_called_once()

    def test_get_user_missing_parameters(self):
        """Test user retrieval with missing parameters."""
        incomplete_params = {
            'name': 'John Doe',
            'email': 'john.doe@example.com'
        }

        response = self.client.get(self.url, incomplete_params)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'The response content must be rendered before it can be iterated over.')


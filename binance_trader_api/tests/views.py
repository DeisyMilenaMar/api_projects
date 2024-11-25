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


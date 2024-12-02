from decimal import Decimal
from smtplib import SMTPException
from unittest.mock import patch
from urllib.parse import urljoin

import requests_mock
from django.conf import settings
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from api.common.exceptions import RequestFailureException
from api.common.vcr_helpers import vcr
from binance_trader_api.factories import TransactionFactory
from binance_trader_api.factories import UserFactory
from binance_trader_api.models import BinanceTraderRequestLog
from binance_trader_api.models import Notification
from binance_trader_api.models import Transaction
from binance_trader_api.models import User
from binance_trader_api.services import NotificationService
from binance_trader_api.services import PriceMonitoringService
from binance_trader_api.services import TransactionService
from binance_trader_api.services import UserService


class TestCreateUserServiceTestCase(TestCase):
    """Test case for User creation."""

    def setUp(self):
        self.user_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
        }

    def test_create_user(self):
        """Test the create_user function."""
        user_created = UserService.create_user(self.user_data)
        self.assertIsInstance(user_created, User)
        self.assertEqual(user_created.name, self.user_data["name"])
        self.assertEqual(user_created.email, self.user_data["email"])


class TestGetUserServiceTestCase(TestCase):
    """Test case for User retrieval."""

    def setUp(self):
        self.user_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
        }

    def test_get_user(self):
        """Test the get_user function."""
        user_created = UserService.create_user(self.user_data)
        self.user_data["user_token"] = user_created.user_token

        retrieved_user = UserService.get_user(self.user_data)
        self.assertIsInstance(retrieved_user, User)
        self.assertEqual(retrieved_user.name, self.user_data["name"])
        self.assertEqual(retrieved_user.email, self.user_data["email"])
        self.assertEqual(retrieved_user.user_token, self.user_data["user_token"])


class TestTransactionServiceTestCase(TestCase):
    """Test suite for creating transactions."""

    def setUp(self):
        self.service = PriceMonitoringService()
        self.user = UserFactory()
        self.transaction_data = {
            "user_token": self.user.user_token,
            "buy_price": 100.0,
            "buy_date": timezone.now(),
            "target_profit_percent": 0.15,
            "status": "created",
        }

    def test_create_transaction_success(self):
        """Ensure TransactionService.create_transaction works for valid data."""
        created_transaction = TransactionService.create_transaction(
            self.transaction_data
        )
        self.assertIsInstance(created_transaction, Transaction)
        self.assertEqual(created_transaction.user, self.user)
        self.assertEqual(
            created_transaction.buy_price, self.transaction_data["buy_price"]
        )
        self.assertEqual(
            created_transaction.buy_date, self.transaction_data["buy_date"]
        )
        self.assertEqual(
            created_transaction.target_profit_percent,
            self.transaction_data["target_profit_percent"],
        )
        self.assertEqual(created_transaction.status, self.transaction_data["status"])

    def test_create_transaction_user_not_found(self):
        """Test creating a transaction fails with an invalid user token."""
        self.transaction_data["user_token"] = "nonexistent_token"

        with self.assertRaises(ValidationError) as context:
            TransactionService.create_transaction(self.transaction_data)

        self.assertEqual(
            str(context.exception), "['User with the provided token does not exist.']"
        )


class TestPriceMonitoringService(TestCase):
    """Test suite for PriceMonitoringService."""

    def setUp(self):
        self.user = UserFactory()
        self.transaction = TransactionFactory(user=self.user, status="pending")
        self.service = PriceMonitoringService()

    @vcr.use_cassette()
    def test_get_binance_client(self):
        """Ensure the Binance client is initialized with the correct configuration."""
        client = self.service.get_binance_client()
        self.assertIsNotNone(client)
        self.assertEqual(
            client.base_url, settings.BINANCE_TRADER_API_REST_CLIENT["BASE_URL"]
        )

    def test_no_pending_transactions(self):
        """Ensure no processing occurs when there are no pending transactions."""
        self.transaction.status = "created"
        self.transaction.save()
        result = self.service.monitor_and_notify_price()
        self.assertEqual(result, "There are no transactions in pending status")

    def test_pending_transaction_price_not_reached(self):
        """Ensure pending transactions remain unchanged
        when the target price is not reached."""
        self.service.monitor_and_notify_price()
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.status, "pending")
        self.assertFalse(
            Notification.objects.filter(transaction=self.transaction).exists()
        )

    def test_get_best_advertiser_valid_response(self):
        """Ensure get_best_advertiser extracts valid
        advertiser data from the response."""
        response_body = {
            "data": [
                {
                    "advertiser": {
                        "userNo": "12345",
                        "nickName": "TraderJoe",
                        "userType": "pro",
                        "monthFinishRate": 95.5,
                        "positiveRate": 99.9,
                        "monthOrderCount": 50,
                    }
                }
            ]
        }
        result = self.service.get_best_advertiser(response_body)
        self.assertEqual(result["user_number"], "12345")
        self.assertEqual(result["nickname"], "TraderJoe")
        self.assertEqual(result["user_type"], "pro")
        self.assertEqual(result["month_finish_rate"], 95.5)
        self.assertEqual(result["positive_rate"], 99.9)
        self.assertEqual(result["month_order_count"], 50)

    def test_get_best_advertiser_empty_data(self):
        """Ensure get_best_advertiser raises an error for empty data."""
        response_body = {"data": []}

        with self.assertRaises(IndexError) as context:
            self.service.get_best_advertiser(response_body)

        self.assertIn("list index out of range", str(context.exception))

    @vcr.use_cassette()
    def test_successful_price_target_reached(self):
        """Ensure transactions are marked ready to sell
        when the target price is reached."""
        self.transaction.buy_price = Decimal("2000.00")
        self.transaction.target_profit_percent = Decimal("0.15")
        self.transaction.usdt_amount_buy = Decimal(10)
        self.transaction.save()

        self.service.monitor_and_notify_price()

        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.status, Transaction.ST_READY_TO_SELL)

        notification = Notification.objects.filter(transaction=self.transaction).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.message, "PRICE_TARGET_REACHED")

        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.user.email])
        self.assertEqual(email.subject, "Price Target Reached for Your Transaction!")

        price_check_log = BinanceTraderRequestLog.objects.filter(
            req_service_slug=BinanceTraderRequestLog.BINANCE_PRICE_SLUG,
            idempotency_token=self.transaction.token_transaction,
        ).first()
        self.assertIsNotNone(price_check_log)
        self.assertEqual(price_check_log.res_http_code, 200)

    @vcr.use_cassette()
    def test_multiple_pending_transactions(self):
        """Ensure multiple pending transactions are processed correctly."""
        TransactionFactory(
            user=self.user,
            status="pending",
            buy_price=Decimal("1000.00"),
            target_profit_percent=Decimal("0.15"),
            usdt_amount_buy=Decimal(10),
        )

        TransactionFactory(
            user=self.user,
            status="pending",
            buy_price=Decimal("1000.00"),
            target_profit_percent=Decimal("0.10"),
            usdt_amount_buy=Decimal(10),
        )
        self.service.monitor_and_notify_price()

        logs = BinanceTraderRequestLog.objects.filter(
            req_service_slug=BinanceTraderRequestLog.BINANCE_PRICE_SLUG
        )
        self.assertEqual(logs.count(), 3)

    @requests_mock.Mocker()
    def test_process_transaction_price_error(self, mocker):
        """Ensure _process_transaction_price handles client errors correctly."""
        mocked_url = urljoin(
            settings.BINANCE_TRADER_API_REST_CLIENT["BASE_URL"],
            settings.BINANCE_TRADER_API_REST_CLIENT["C2C_SEARCH_ENDPOINT"],
        )
        mocker.post(
            mocked_url,
            json={"message": "Invalid request", "code": 400},
            status_code=400,
        )

        self.transaction.save()
        client = self.service.get_binance_client()

        with self.assertRaises(RequestFailureException):
            self.service._process_transaction_price(client, self.transaction)

    @patch("binance_trader_api.services.send_mail")
    def test_send_email_notification_failure_simple(self, mock_send_mail):
        """Ensure send_mail is called and raises SMTPException."""
        mock_send_mail.side_effect = SMTPException("SMTP error")

        user = User.objects.create(name="Test User", email="d2marug@gmail.com")
        transaction = Transaction.objects.create(
            user=user,
            buy_price=Decimal("100.0"),
            target_profit_percent=Decimal("0.10"),
            usdt_amount_buy=Decimal(10),
            buy_date=timezone.now(),
        )

        advertiser_details = {"nickname": "Test Advertiser"}

        notification_service = NotificationService()

        notification_service.send_email_notification(transaction, advertiser_details)

        mock_send_mail.assert_called_once()
        req = BinanceTraderRequestLog.objects.get(
            req_service_slug=BinanceTraderRequestLog.EMAIL_SENDING_SLUG
        )
        self.assertEqual(req.res_result_message, "Failed to send email: SMTP error")

    @patch("binance_trader_api.services.send_mail")
    def test_send_email_notification_no_emails_sent(self, mock_send_mail):
        mock_send_mail.return_value = 0

        user = User.objects.create(name="Test User", email="test@example.com")
        transaction = Transaction.objects.create(
            user=user,
            buy_price=Decimal("100.0"),
            target_profit_percent=Decimal("0.10"),
            usdt_amount_buy=Decimal(10),
            buy_date=timezone.now(),
        )
        advertiser_details = {"nickname": "Test Advertiser"}

        notification_service = NotificationService()

        notification_service.send_email_notification(transaction, advertiser_details)

        mock_send_mail.assert_called_once()
        req = BinanceTraderRequestLog.objects.get(
            req_service_slug=BinanceTraderRequestLog.EMAIL_SENDING_SLUG
        )
        self.assertIn("Failed to send email", req.res_result_message)

from decimal import Decimal

# Django imports
from django.test import TestCase
from django.core.exceptions import ValidationError

# Factory imports
from binance_trader_api.factories import UserFactory
from binance_trader_api.factories import AdvertiserFactory
from binance_trader_api.factories import AdvertisementFactory
from binance_trader_api.factories import TransactionFactory
from binance_trader_api.factories import NotificationFactory

# Model imports
from binance_trader_api.models import User
from binance_trader_api.models import Advertiser
from binance_trader_api.models import Advertisement
from binance_trader_api.models import Transaction
from binance_trader_api.models import Notification
from binance_trader_api.models import BinanceTraderRequestLog


class UserTestCase(TestCase):
    """Tests for the User model."""

    def test_user_creation_with_short_name(self):
        """Ensure that creating a user with a name shorter than 2 characters raises a ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            user = UserFactory(name='J')
            user.full_clean()
        self.assertIn("Ensure this value has at least 2 characters", str(cm.exception))

    def test_valid_user_creation(self):
        """Ensure that a User instance can be created with valid data."""
        user = UserFactory()
        self.assertIsInstance(user, User)
        self.assertTrue(user.email)
        self.assertTrue(user.user_token)

    def test_user_token_uniqueness(self):
        """Ensure that each User instance has a unique user_token."""
        user1 = UserFactory()
        user2 = UserFactory()
        self.assertNotEqual(user1.user_token, user2.user_token)


class AdvertiserTestCase(TestCase):
    """Tests for the Advertiser model."""

    def test_advertiser_creation(self):
        """Ensure that an Advertiser instance can be created with valid data."""
        advertiser = AdvertiserFactory()
        self.assertIsInstance(advertiser, Advertiser)
        self.assertTrue(advertiser.user_number)
        self.assertIsInstance(advertiser.nickname, str)
        self.assertIsInstance(advertiser.month_finish_rate, Decimal)

    def test_month_finish_invalid_rate_limit(self):
        """Ensure that a month_finish_rate above 1 raises a ValidationError."""
        advertiser = AdvertiserFactory()
        advertiser.month_finish_rate=Decimal(10.99)
        with self.assertRaises(ValidationError) as cm:
            advertiser.full_clean()
        self.assertIn("Ensure this value is less than or equal to 1", str(cm.exception))

    def test_positive_rate_limit(self):
        """Ensure that a valid positive_rate can be set for an Advertiser."""
        advertiser = AdvertiserFactory(positive_rate=Decimal(0.98))
        self.assertEqual(advertiser.positive_rate, Decimal(0.98))


class AdvertisementTestCase(TestCase):
    """Tests for the Advertisement model."""

    def test_foreign_key_relationships(self):
        """Ensure that an Advertisement instance is linked to a valid Advertiser."""
        advertisement = AdvertisementFactory()
        self.assertIsInstance(advertisement.advertiser, Advertiser)

    def test_advertisement_creation(self):
        """Ensure that an Advertisement instance can be created with valid data."""
        advertisement = AdvertisementFactory()
        self.assertIsInstance(advertisement, Advertisement)
        self.assertTrue(advertisement.ad_number)
        self.assertTrue(advertisement.price)


class TransactionTestCase(TestCase):
    """Tests for the Transaction model."""

    def test_transaction_creation(self):
        """Ensure that a Transaction instance can be created with valid data."""
        transaction = TransactionFactory()
        self.assertTrue(transaction.token_transaction)

    def test_transaction_status_choice(self):
        """Ensure that only valid status choices are allowed for Transaction."""
        transaction = TransactionFactory()
        transaction.full_clean()
        self.assertEqual(transaction.status, Transaction.ST_CREATED)

    def test_transaction_token_uniqueness(self):
        """Ensure that token_transaction is unique for each Transaction instance."""
        transaction1 = TransactionFactory()
        transaction2 = TransactionFactory()
        self.assertNotEqual(transaction1.token_transaction, transaction2.token_transaction)

    def test_transaction_creation_with_invalid_target_profit_percent(self):
        """Ensure that a negative target_profit_percent raises a ValidationError."""
        transaction = TransactionFactory()
        transaction.target_profit_percent=Decimal(-1)
        with self.assertRaises(ValidationError) as cm:
            transaction.full_clean()
        self.assertIn("Ensure this value is greater than or equal to 0.", str(cm.exception))

    def test_transaction_creation_with_invalid_status(self):
        """Ensure that an invalid status raises a ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            transaction = TransactionFactory(status='invalid')
            transaction.full_clean()
        self.assertIn("Value 'invalid' is not a valid choice.", str(cm.exception))

    def test_create_valid_transaction(self):
        """Ensure that a Transaction instance with valid data is created successfully."""
        transaction = TransactionFactory()
        self.assertIsInstance(transaction, Transaction)
        self.assertIsInstance(transaction.user, User)
        self.assertIsInstance(transaction.advertisement, Advertisement)
        self.assertIsInstance(transaction.token_transaction, str)
        self.assertIsInstance(transaction.buy_price, Decimal)
        self.assertIsInstance(transaction.target_profit_percent, Decimal)
        self.assertGreater(transaction.target_profit_percent, Decimal(0.01))
        self.assertLess(transaction.target_profit_percent, Decimal(100))


class NotificationTestCase(TestCase):
    """Tests for the Notification model."""

    def test_notification_creation(self):
        """Ensure that a Notification instance can be created with valid data."""
        notification = NotificationFactory()
        self.assertIsInstance(notification, Notification)
        self.assertTrue(notification.message)
        self.assertIsNotNone(notification.notified_at)

    def test_foreign_key_relationship(self):
        """Ensure that a Notification instance has a valid foreign key to a Transaction and User."""
        notification = NotificationFactory()
        self.assertIsInstance(notification.transaction, Transaction)
        self.assertIsInstance(notification.user, User)

    def test_create_valid_notification(self):
        """Ensure that a Notification instance with valid data is created successfully."""
        notification = NotificationFactory()
        self.assertIsInstance(notification, Notification)
        self.assertIsInstance(notification.user, User)
        self.assertIsInstance(notification.transaction, Transaction)
        self.assertIsInstance(notification.message, str)


class BinanceTraderRequestLogTestCase(TestCase):
    """Tests for the BinanceTraderRequestLog model."""

    def setUp(self):
        """Set up valid data for BinanceTraderRequestLog tests."""
        self.valid_data = {
            "idempotency_token": "abc123",
            "req_service_slug": BinanceTraderRequestLog.USER_CREATION_SLUG,
            "req_http_body": {"example_key": "example_value"},
            "res_http_body": {"result": "success"},
            "res_http_code": 200,
            "res_result_message": "Operation completed successfully",
            "res_result_code": "200_OK"
        }

    def test_binance_trader_request_log_creation_with_invalid_slug(self):
        """Ensure that an invalid req_service_slug raises a ValidationError."""
        request_log = BinanceTraderRequestLog.objects.create(**self.valid_data)
        with self.assertRaises(ValidationError) as cm:
            request_log.req_service_slug = "invalid_slug"
            request_log.full_clean()
        self.assertIn("Value 'invalid_slug' is not a valid choice.", str(cm.exception))

    def test_binance_trader_request_log_creation_with_long_token(self):
        """Ensure that an idempotency_token exceeding the max length raises a ValidationError."""
        request_log = BinanceTraderRequestLog.objects.create(**self.valid_data)
        request_log.idempotency_token = 'a' * 129
        with self.assertRaises(ValidationError) as cm:
            request_log.full_clean()
        self.assertIn("Ensure this value has at most 50 characters (it has 129).", str(cm.exception))

    def test_create_valid_binance_trader_request_log(self):
        """Ensure that a BinanceTraderRequestLog instance with valid data is created successfully."""
        request_log = BinanceTraderRequestLog.objects.create(**self.valid_data)
        self.assertEqual(request_log.idempotency_token, self.valid_data["idempotency_token"])
        self.assertEqual(request_log.req_service_slug, self.valid_data["req_service_slug"])
        self.assertEqual(request_log.req_http_body, self.valid_data["req_http_body"])
        self.assertEqual(request_log.res_http_body, self.valid_data["res_http_body"])
        self.assertEqual(request_log.res_http_code, self.valid_data["res_http_code"])
        self.assertEqual(request_log.res_result_message, self.valid_data["res_result_message"])
        self.assertEqual(request_log.res_result_code, self.valid_data["res_result_code"])

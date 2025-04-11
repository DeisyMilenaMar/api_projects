import json
import logging
from decimal import Decimal
from smtplib import SMTPException
from time import sleep

from constance import config
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from api.common.exceptions import RequestFailureException
from api.common.exceptions import UnknownResultException
from binance_trader_api.binance_client import BinanceClient
from binance_trader_api.models import BinanceTraderRequestLog
from binance_trader_api.models import Notification
from binance_trader_api.models import Transaction
from binance_trader_api.models import User

logger = logging.getLogger(__name__)

EMAIL_TEMPLATE_PATH = "emails/price_target_reached.html"


class UserService:
    """Service class for managing User-related operations."""

    @staticmethod
    def create_user(data: dict):
        """
        Creates a new user with the provided data.
        """
        return User.objects.create(name=data.get("name"), email=data.get("email"))

    @staticmethod
    def get_user(data: dict):
        """
        Retrieves a user based on 'name', 'email', and 'user_token'.
        """
        return User.objects.get(
            name=data.get("name"),
            email=data.get("email"),
            user_token=data.get("user_token"),
        )


class TransactionService:
    """Service to manage operations related to transactions."""

    @staticmethod
    def create_transaction(data: dict):
        """
        Create a new transaction with the provided data.
        """

        user_token = data.get("user_token", "")
        user = User.objects.filter(user_token=user_token).first()

        if not user:
            logger.warning(
                "User not found with token: %s", extra={"token_user": user_token}
            )
            raise ValidationError("User with the provided token does not exist.")

        return Transaction.objects.create(
            user=user,
            buy_price=data.get("buy_price", 0.0),
            buy_date=data.get("buy_date"),
            usdt_amount_buy=data.get("usdt_amount_buy", 0.0),
            target_profit_percent=data.get("target_profit_percent", 0.0),
            status=data.get("status", Transaction.ST_PENDING),
        )


class PriceMonitoringService:
    """Service to monitor transaction prices and handle notifications."""

    @staticmethod
    def get_binance_client():
        """Initialize and return a Binance API client."""
        client_settings = settings.BINANCE_TRADER_API_REST_CLIENT
        return BinanceClient(
            base_url=client_settings["BASE_URL"],
            timeout=config.BINANCE_TRADER_API_REST_CLIENT_TIMEOUT_SECS,
        )

    @staticmethod
    def get_price_request_params(transaction: Transaction):
        """Generate parameters for price request."""
        return {
            "fiat": config.BINANCE_FIAT,
            "page": 1,
            "rows": config.BINANCE_ROWS,
            "transAmount": float(transaction.buy_price * transaction.usdt_amount_buy),
            "tradeType": config.BINANCE_TRADE_TYPE,
            "asset": config.BINANCE_ASSET,
            "countries": [],
            "proMerchantAds": False,
            "shieldMerchantAds": False,
            "filterType": config.BINANCE_FILTER_TYPE,
            "periods": [],
            "additionalKycVerifyFilter": 0,
            "publisherType": config.BINANCE_PUBLISHER_TYPE,
            "payTypes": config.BINANCE_PAYTYPES.split(","),
            "classifies": config.BINANCE_CLASSIFIES.split(","),
        }

    def create_price_check_log(
        self,
        transaction: Transaction,
        request_body: str,
        response_body: dict,
        status_code: int,
    ):
        """Create a log entry for price check request."""
        return BinanceTraderRequestLog.objects.create(
            req_service_slug=BinanceTraderRequestLog.BINANCE_PRICE_SLUG,
            idempotency_token=transaction.token_transaction,
            req_http_body=request_body,
            res_http_body=response_body,
            res_http_code=status_code,
            res_result_message=response_body.get("message", ""),
            res_result_code=response_body.get("code"),
        )

    @staticmethod
    def get_best_advertiser(response_body: dict):
        """Extract best advertiser information from response."""
        try:
            advertiser_data = response_body.get("data", [{}])[0].get("advertiser", {})
            return {
                "user_number": advertiser_data.get("userNo", ""),
                "nickname": advertiser_data.get("nickName", ""),
                "user_type": advertiser_data.get("userType", ""),
                "month_finish_rate": advertiser_data.get("monthFinishRate", 0.0),
                "positive_rate": advertiser_data.get("positiveRate", 0.0),
                "month_order_count": advertiser_data.get("monthOrderCount", 0),
            }
        except TypeError as exc:
            logger.error(f"Error extracting advertiser information: {str(exc)}")
            return {}

    def monitor_and_notify_price(self):
        """
        Monitor pending transactions and notify users when target price is reached.
        """
        pending_transactions = Transaction.objects.filter(status=Transaction.ST_PENDING)

        if not pending_transactions.exists():
            return "There are no transactions in pending status"

        client = self.get_binance_client()

        for transaction in pending_transactions:
            try:
                self._process_transaction_price(client, transaction)
            except (RequestFailureException, UnknownResultException) as exc:
                self._handle_monitoring_error(transaction, exc)

        return f"Quantity of transactions processed were {len(pending_transactions)}"

    def _process_transaction_price(
        self, client: BinanceClient, transaction: Transaction
    ):
        """Process price check for a single transaction."""
        request_params = self.get_price_request_params(transaction)
        response = client.get_price(**request_params)
        sleep(config.BINANCE_TRADER_SLEEP_SECS)

        try:
            request_body = json.loads(
                response.request.body
                if isinstance(response.request.body, str)
                else (
                    response.request.body.decode("utf-8")
                    if hasattr(response, "request")
                    else ""
                )
            )
            response_body = response.json() if response.content else {}

        except json.JSONDecodeError as exc:
            logger.error(f"Error al decodificar JSON de la respuesta: {str(exc)}")
            return

        status_code = response.status_code

        price_log = self.create_price_check_log(
            transaction, request_body, response_body, status_code
        )

        if price_log.res_http_code != 200:
            logger.error(
                "Failed to get current price from Binance",
                extra={
                    "response_code": price_log.res_http_code,
                    "transaction_id": transaction.id,
                },
            )
            return

        self._analyze_and_notify(transaction, response_body)

    def _analyze_and_notify(self, transaction: Transaction, response_body: dict):
        """Analyze transaction price and notify if target is reached."""

        target_price = Decimal(transaction.buy_price) * (
            1 + Decimal(transaction.target_profit_percent)
        )
        try:
            price_data = response_body.get("data", [{}])[0]
            adv_price_str = price_data.get("adv", {}).get("price", 0)

            # Convert adv_price to Decimal
            adv_price = Decimal(adv_price_str)

            if adv_price >= target_price:
                transaction.status = Transaction.ST_READY_TO_SELL
                transaction.save()

                NotificationService().send_email_notification(
                    transaction,
                    self.get_best_advertiser(response_body),
                )

        except (IndexError, KeyError) as exc:
            logger.error(f"Error analyzing transaction {transaction.id}: {str(exc)}")

    def _handle_monitoring_error(self, transaction: Transaction, exc: Exception):
        """Handle and log monitoring errors."""
        logger.error(
            f"Error processing transaction {transaction.id}: {str(exc), type(exc)}"
        )
        BinanceTraderRequestLog.objects.create(
            req_service_slug=BinanceTraderRequestLog.BINANCE_P2P_SEARCH_SLUG,
            req_http_body={
                "transaction_id": transaction.id,
                "error": str(exc),
                "error_type": type(exc).__name__,
            },
            res_result_message=f"Error in price monitoring: {str(exc)}",
        )


class NotificationService:
    """Service to handle user notifications."""

    @staticmethod
    def create_notification(transaction: Transaction):
        """Create notification for target price reached."""
        notification = Notification.objects.create(
            user=transaction.user,
            transaction=transaction,
            message="PRICE_TARGET_REACHED",
            notified_at=timezone.now(),
        )

        BinanceTraderRequestLog.objects.create(
            req_service_slug=BinanceTraderRequestLog.NOTIFICATION_CREATION_SLUG,
            req_http_body={
                "transaction_token": transaction.token_transaction,
                "user_token": transaction.user.user_token,
            },
            res_result_message="Notification created successfully",
        )
        return notification

    def send_email_notification(self, transaction: Transaction, advertiser_details):
        """Send email notification to user."""
        subject = "Price Target Reached for Your Transaction!"
        context = {
            "user_name": transaction.user.name,
            "buy_price": transaction.buy_price,
            "target_profit_percent": transaction.target_profit_percent,
            "target_price": transaction.buy_price
            * (1 + transaction.target_profit_percent),
            "advertiser_user_number": advertiser_details.get("user_number", ""),
            "advertiser_nickname": advertiser_details.get("nickname", ""),
            "advertiser_user_type": advertiser_details.get("user_type", ""),
            "advertiser_month_finish_rate": advertiser_details.get(
                "month_finish_rate", 0.0
            ),
            "advertiser_positive_rate": advertiser_details.get("positive_rate", 0.0),
            "advertiser_month_order_count": advertiser_details.get(
                "month_order_count", 0
            ),
        }

        try:
            html_message = render_to_string(EMAIL_TEMPLATE_PATH, context)
            plain_message = strip_tags(html_message)

            result = send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [transaction.user.email],
                html_message=html_message,
            )

            if result == 0:
                logger.warning("No emails were sent")
                raise ValidationError("send_mail failed, result different from 1")

            NotificationService.create_notification(transaction)
            BinanceTraderRequestLog.objects.create(
                req_service_slug=BinanceTraderRequestLog.EMAIL_SENDING_SLUG,
                req_http_body={
                    "email": transaction.user.email,
                    "subject": subject,
                    "transaction_id": transaction.id,
                },
                res_result_message="Email notification sent successfully",
            )

        except (ValidationError, ValueError, SMTPException) as exc:
            logger.error(
                f"Failed to send email notification for transaction "
                f"{transaction.id}: {str(exc)}"
            )

            # Create a log entry for the failed email
            BinanceTraderRequestLog.objects.create(
                req_service_slug=BinanceTraderRequestLog.EMAIL_SENDING_SLUG,
                req_http_body={
                    "email": transaction.user.email,
                    "subject": subject,
                    "transaction_id": transaction.id,
                },
                res_result_message=f"Failed to send email: {str(exc)}",
            )

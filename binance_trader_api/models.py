from django.core.validators import RegexValidator, MinLengthValidator, MinValueValidator, MaxValueValidator
from functools import partial
from django.db import models
from django.db.models import JSONField
from api.common.models import AutoCreatedUpdatedMixin
from api.common.helpers import generate_token

class User(AutoCreatedUpdatedMixin):
    """
    Model representing a user with basic information.
    """
    name = models.CharField(
        max_length=60,
        validators=[
            RegexValidator(
                regex=r'^[\w á-úÁ-Ú]*$',
                message="Name must only contain letters, spaces, and underscores."
            ),
            MinLengthValidator(2)
        ],
        help_text="User's full name."
    )
    email = models.EmailField(
        unique=True,
        help_text="Unique email address used to identify the user."
    )
    user_token = models.CharField(
        max_length=128,
        unique=True,
        default=partial(generate_token, prefix='usr', with_date=True),
        help_text="Unique token generated for the user."
    )


class Advertiser(AutoCreatedUpdatedMixin):
    """
    Model representing an advertiser's profile information.
    """
    user_number = models.CharField(
        max_length=50,
        help_text="Identification number of the advertiser."
    )
    nickname = models.CharField(
        max_length=50,
        help_text="Nickname of the advertiser."
    )
    user_type = models.CharField(
        max_length=50,
        help_text="Type of advertiser (e.g., individual, company)."
    )
    month_finish_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        help_text="Monthly transaction completion rate."
    )
    positive_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        help_text="Percentage of positive feedback."
    )
    month_order_count = models.IntegerField(
        help_text="Number of orders completed in the month."
    )


class Advertisement(AutoCreatedUpdatedMixin):
    """
    Model representing an advertisement for trading assets.
    """
    advertiser = models.ForeignKey(
        Advertiser,
        on_delete=models.DO_NOTHING,
        related_name="advertisements",
        help_text="Advertiser responsible for the advertisement."
    )
    ad_number = models.CharField(
        max_length=50,
        help_text="Unique identifier of the advertisement."
    )
    trade_type = models.CharField(
        max_length=50,
        help_text="Type of trade (e.g., buy or sell)."
    )
    asset = models.CharField(
        max_length=50,
        help_text="Asset being traded (e.g., USDT)."
    )
    fiat_unit = models.CharField(
        max_length=10,
        help_text="Fiat currency used in the advertisement (e.g., USD)."
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price per unit of the asset."
    )
    min_trade_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Minimum trade limit."
    )
    max_trade_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum trade limit."
    )


class Transaction(AutoCreatedUpdatedMixin):
    """
    Model tracking user's transactions, including details and current status.
    """
    ST_CREATED = 'created'
    ST_PENDING = 'pending'
    ST_READY_TO_SELL = 'ready_to_sell'
    ST_COMPLETED = 'completed'
    
    TRANSACTION_CHOICES = [
        (ST_CREATED, ST_CREATED),
        (ST_PENDING, ST_PENDING),
        (ST_READY_TO_SELL, ST_READY_TO_SELL),
        (ST_COMPLETED, ST_COMPLETED),
    ]
    token_transaction = models.CharField(
        max_length=64,
        unique=True,
        default=partial(generate_token, prefix='trx', with_date=True),
        help_text="Unique transaction token."
    )
    user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="transactions",
        help_text="User who initiated the transaction."
    )
    advertisement = models.ForeignKey(
        Advertisement,
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        related_name="transactions",
        help_text="Associated advertisement for the transaction."
    )
    buy_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price at which the item was bought."
    )
    buy_date = models.DateTimeField(
        help_text="Date and time of purchase."
    )
    target_profit_percent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0.01),
            MaxValueValidator(100)
        ],
        help_text="Target profit percentage for the transaction (e.g., 15.00 for 15%)."
    )
    notification_sent = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Timestamp when notification was sent."
    )
    status = models.CharField(
        max_length=16,
        choices=TRANSACTION_CHOICES,
        help_text="Current transaction status."
    )


class Notification(AutoCreatedUpdatedMixin):
    """
    Model representing a user notification related to a transaction.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="notifications",
        help_text="User to be notified."
    )
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.DO_NOTHING,
        related_name="notifications",
        help_text="Transaction related to this notification."
    )
    message = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        help_text="Content of the notification message."
    )
    notified_at = models.DateTimeField(
        help_text="Timestamp when notification was sent."
    )


class BinanceTraderRequestLog(AutoCreatedUpdatedMixin):
    """
    Model for logging requests and responses to/from Binance trading services.
    """
    USER_CREATION = "user_creation"
    TRANSACTION_CREATION = "transaction_creation"
    BINANCE_PRICE = "binance_price_check"
    BINANCE_P2P_SEARCH = "binance_P2P_advertisement_search"
    PRICE_ANALYSIS = "price_analysis"
    NOTIFICATION_CREATION = "notification_creation"
    EMAIL_SENDING = "email_sending"
    
    ACTION_CHOICES = [
        (USER_CREATION, USER_CREATION),
        (TRANSACTION_CREATION, TRANSACTION_CREATION),
        (BINANCE_PRICE, BINANCE_PRICE),
        (BINANCE_P2P_SEARCH, BINANCE_P2P_SEARCH),
        (PRICE_ANALYSIS, PRICE_ANALYSIS),
        (NOTIFICATION_CREATION, NOTIFICATION_CREATION),
        (EMAIL_SENDING, EMAIL_SENDING)
    ]
    idempotency_token = models.CharField(
        max_length=64,
        unique=True,
        default=partial(generate_token, prefix='idmp', with_date=True),
        help_text="Unique idempotency token for request uniqueness."
    )
    req_service_slug = models.CharField(
        max_length=40,
        choices=ACTION_CHOICES,
        help_text="Specifies the type of service request made."
    )
    req_http_body = JSONField(
        blank=True,
        null=True,
        help_text="HTTP request body content, if applicable."
    )
    res_http_body = JSONField(
        blank=True,
        null=True,
        help_text="HTTP response body content, if applicable."
    )
    res_http_code = models.IntegerField(
        blank=True,
        null=True,
        help_text="HTTP status code from the response."
    )
    res_result_message = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        help_text="Detailed error or result message from the service."
    )
    res_result_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Service response code, if available."
    )

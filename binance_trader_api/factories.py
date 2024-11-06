import datetime
import secrets

from django.utils import timezone

import factory
from factory import Faker
from factory.django import DjangoModelFactory

from .models import User
from .models import Advertiser
from .models import Advertisement
from .models import Transaction
from .models import Notification

from api.common.helpers import generate_token


class UserFactory(DjangoModelFactory):
    """
    Factory for creating User instances with randomized data for testing purposes.
    Uses Faker for generating fake name and email, and a custom function for a unique user token.
    """
    name = Faker('name')
    email = Faker('email')
    user_token = factory.LazyFunction(lambda: generate_token(prefix='usr', with_date=True))

    class Meta:
        model = User


class AdvertiserFactory(DjangoModelFactory):
    """
    Factory for generating Advertiser instances with random data.
    This includes fields like user_number, nickname, user_type, and ratings.
    """
    user_number = factory.LazyFunction(lambda: secrets.token_hex(16))
    nickname = Faker('user_name')
    user_type = Faker('random_element', elements=['individual', 'company'])
    month_finish_rate = Faker('pydecimal', left_digits=1, right_digits=9, positive=True, max_value=1)
    positive_rate = Faker('pydecimal', left_digits=1, right_digits=9, positive=True, max_value=1)
    month_order_count = Faker('random_int', min=0, max=100000)

    class Meta:
        model = Advertiser


class AdvertisementFactory(DjangoModelFactory):
    """
    Factory for creating Advertisement instances associated with an Advertiser.
    Fields include ad_number, trade type, asset, fiat unit, and price limits.
    """
    advertiser = factory.SubFactory(AdvertiserFactory)
    ad_number = Faker('isbn10')
    trade_type = Faker('random_element', elements=['buy', 'sell'])
    asset = Faker('random_element', elements=['USDT', 'BTC', 'ETH'])
    fiat_unit = Faker('currency_code')
    price = Faker('pydecimal', left_digits=8, right_digits=2, positive=True)
    min_trade_limit = Faker('pydecimal', left_digits=8, right_digits=2, positive=True)
    max_trade_limit = Faker('pydecimal', left_digits=8, right_digits=2, positive=True)

    class Meta:
        model = Advertisement


class TransactionFactory(DjangoModelFactory):
    """
    Factory for creating Transaction instances that link Users with Advertisements.
    Includes fields like token_transaction, buy_price, and target profit percentage.
    """
    token_transaction = factory.LazyFunction(lambda: generate_token(prefix='trx', with_date=True))
    user = factory.SubFactory(UserFactory)
    advertisement = factory.SubFactory(AdvertisementFactory)
    buy_price = Faker('pydecimal', left_digits=8, right_digits=2, positive=True)
    buy_date = timezone.now() - datetime.timedelta(days=30)
    target_profit_percent = Faker('pydecimal', left_digits=8, right_digits=2, positive=True, min_value=0.01, max_value=100)
    notification_sent = timezone.now()

    class Meta:
        model = Transaction


class NotificationFactory(DjangoModelFactory):
    """
    Factory for generating Notification instances associated with Users and Transactions.
    Fields include a message and notification timestamp.
    """
    user = factory.SubFactory(UserFactory)
    transaction = factory.SubFactory(TransactionFactory)
    message = Faker('sentence')
    notified_at = timezone.now()

    class Meta:
        model = Notification


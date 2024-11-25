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
    """Factory for User model with unique token and randomized data."""
    name = Faker('name')
    email = Faker('email')

    class Meta:
        model = User


class AdvertiserFactory(DjangoModelFactory):
    """Factory for Advertiser model with randomized user data."""
    user_number = factory.LazyFunction(lambda: secrets.token_hex(16))
    nickname = Faker('user_name')
    user_type = 'company'
    month_finish_rate = Faker('pydecimal', left_digits=1, right_digits=9, positive=True, max_value=1)
    positive_rate = Faker('pydecimal', left_digits=1, right_digits=9, positive=True, max_value=1)
    month_order_count = Faker('random_int', min=0, max=100000)

    class Meta:
        model = Advertiser


class AdvertisementFactory(DjangoModelFactory):
    """Factory for Advertisement model with randomized trade data."""
    advertiser = factory.SubFactory(AdvertiserFactory)
    ad_number = Faker('numerify', text='###################')
    trade_type = 'sell'
    asset = 'USDT'
    fiat_unit = Faker('currency_code')
    price = Faker('pydecimal', left_digits=8, right_digits=2, positive=True)
    min_trade_limit = Faker('pydecimal', left_digits=8, right_digits=2, positive=True)
    max_trade_limit = Faker('pydecimal', left_digits=8, right_digits=2, positive=True)

    class Meta:
        model = Advertisement


class TransactionFactory(DjangoModelFactory):
    """Factory for Transaction model linking Users and Advertisements."""
    token_transaction = factory.LazyFunction(lambda: generate_token(prefix='trx', with_date=True))
    user = factory.SubFactory(UserFactory)
    advertisement = factory.SubFactory(AdvertisementFactory)
    buy_price = Faker('pydecimal', left_digits=8, right_digits=2, positive=True)
    buy_date = factory.LazyFunction(lambda: timezone.now() - datetime.timedelta(days=30))
    target_profit_percent = Faker('pydecimal', left_digits=1, right_digits=2, positive=True, max_value=1)
    notification_sent = factory.LazyFunction(timezone.now)
    status = 'created'

    class Meta:
        model = Transaction


class NotificationFactory(DjangoModelFactory):
    """Factory for Notification model associated with Users and Transactions."""
    user = factory.SubFactory(UserFactory)
    transaction = factory.SubFactory(TransactionFactory)
    message = Faker('sentence')
    notified_at = factory.LazyFunction(timezone.now)

    class Meta:
        model = Notification


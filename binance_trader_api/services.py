import logging
from django.core.exceptions import ValidationError
from binance_trader_api.models import User
from binance_trader_api.models import Transaction
from binance_trader_api.models import BinanceTraderRequestLog


logger = logging.getLogger(__name__)

class UserService:
    """Service class for managing User-related operations."""

    @staticmethod
    def create_user(data: dict):
        """Creates a new user with the provided data.
        """
        return User.objects.create(
            name=data.get('name'),
            email=data.get('email')
        )

    @staticmethod
    def get_user(data: dict):
        """Retrieves a user based on 'name', 'email', and 'user_token'.
        """
        return User.objects.get(
            name=data.get('name'),
            email=data.get('email'),
            user_token=data.get('user_token')
        )


class TransactionService:
    @staticmethod
    def create_transaction(data: dict):
        """Create a new transaction with the provided data."""
        user = User.objects.filter(user_token=data.get('user_token')).first()
        if not user:
            logger.warning(
                "User not found with token: %s",
                extra={'token_user': data.get('token_user')}
            )
            raise ValidationError("User with the provided token does not exist.")

        transaction = Transaction.objects.create(
            user = user,
            buy_price=data.get('buy_price'),
            buy_date=data.get('buy_date'),
            target_profit_percent=data.get('target_profit_percent'),
            status=data.get('status')
        )
        return transaction

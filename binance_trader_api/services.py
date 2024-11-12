import logging
from binance_trader_api.models import User

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
    pass
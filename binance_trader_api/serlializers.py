from rest_framework import serializers

from binance_trader_api.models import Transaction
from binance_trader_api.models import User


class TransactionRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for transaction creation or updates.
    Validates the incoming transaction details from the user.
    """

    user_token = serializers.CharField(required=True)

    class Meta:
        model = Transaction
        fields = [
            "buy_price",
            "buy_date",
            "usdt_amount_buy",
            "target_profit_percent",
            "status",
            "user_token",
        ]


class TransactionResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for presenting transaction details.
    Maps directly to the Transaction model.
    """

    class Meta:
        model = Transaction
        fields = [
            "buy_price",
            "buy_date",
            "usdt_amount_buy",
            "target_profit_percent",
            "status",
        ]


class UserCreateRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for user creation requests.
    Validates the incoming user details.
    """

    class Meta:
        model = User
        fields = ["name", "email"]


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user retrieval requests.
    """

    class Meta:
        model = User
        fields = ["name", "email", "user_token"]

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
import logging

from api.common.views import BaseServiceView

from binance_trader_api.serlializers import TransactionRequestSerializer
from binance_trader_api.serlializers import TransactionResponseSerializer

from binance_trader_api.services import TransactionService


logger = logging.getLogger(__name__)

class TransactionCreateView(BaseServiceView):
    """
    API View for creating a new transaction.
    Inherits common validation and error handling from BaseServiceView.
    """
    request_serializer = TransactionRequestSerializer
    response_serializer = TransactionResponseSerializer
    http_method = 'POST'

    def process_request(self, validated_data, request):
        """
        Process the transaction creation logic.
        - Use the `TransactionService` to create the transaction.
        - Return the created transaction and HTTP status.
        """
        try:
            transaction = TransactionService.create_transaction(validated_data)
            return transaction, status.HTTP_201_CREATED
    
        except ValidationError as exc:
            logger.error(
                "Validation error while creating transaction",
                extra={
                    'error': str(exc),
                    'user_token': validated_data.get('user_token')
                }
            )
            raise

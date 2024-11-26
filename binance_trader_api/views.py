from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
import logging

from api.common.views import BaseServiceView

from binance_trader_api.serlializers import TransactionRequestSerializer
from binance_trader_api.serlializers import TransactionResponseSerializer
from binance_trader_api.serlializers import UserCreateRequestSerializer
from binance_trader_api.serlializers import  UserSerializer

from binance_trader_api.models import User

from binance_trader_api.services import TransactionService
from binance_trader_api.services import UserService


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

class UserCreateView(BaseServiceView):
    """
    API View for creating a new user.
    Inherits common validation and error handling from BaseServiceView.
    """
    request_serializer = UserCreateRequestSerializer
    response_serializer = UserSerializer
    http_method = 'POST'
    
    def process_request(self, validated_data, request):
        "Process the validated request data to create a new user."
        try:
            user = UserService.create_user(validated_data)
            return user, status.HTTP_201_CREATED
        
        except ValidationError as exc:
            logger.error(
                "Error creating user",
                extra={
                    'error': str(exc),
                    'name': validated_data.get('name'),
                    'email': validated_data.get('email')
                }
            )
            raise

class UserGetView(BaseServiceView):
    """
    API View for retrieving user details.
    """
    request_serializer = UserSerializer
    response_serializer = UserSerializer
    http_method = 'GET'
        
    def process_request(self, validated_data, request):
        "Process the validated request data to create a new user."
        try:
            user = UserService.get_user(validated_data)
            return user, status.HTTP_200_OK
        except User.DoesNotExist as exc:
            
            logger.warning(
                "User not found",
                extra={
                    'error': str(exc),
                    'email': validated_data.get('email', 'N/A')
                }
            )
            return Response({
                'error': 'User not found with the provided details'
            }, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as exc:
            return Response({
                'error': f'Missing required field: {str(exc)}'
            }, status=status.HTTP_400_BAD_REQUEST)

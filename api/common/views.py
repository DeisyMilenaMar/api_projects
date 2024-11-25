import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

logger = logging.getLogger(__name__)

class BaseServiceView(APIView):
    """
    Standardized APIView for request validation, logging, and error handling.
    """
    request_serializer = None
    response_serializer = None
    http_method = None

    def validate_request(self, request):
        """
        Validate request data using the defined request serializer.
        """
        if not self.request_serializer:
            return request.data

        serializer = self.request_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def process_request(self, validated_data, request):
        """
        Subclasses must define this to handle request logic.
        """
        raise NotImplementedError("You must implement `process_request` in your subclass.")

    def handle_request(self, request, method):
        """
        Handle the request: validate data, process logic, and handle errors.
        """
        try:
            data = self.validate_request(request)
            logger.info(f"{method} request validated successfully.")
            response_data, status_code = self.process_request(data, request)
            serialized_data = self.response_serializer(response_data).data if self.response_serializer else response_data
            return Response(serialized_data, status=status_code)
        except Exception as e:
            logger.error(f"Error in {method} request: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        return self.handle_request(request, 'POST')

    def get(self, request, *args, **kwargs):
        return self.handle_request(request, 'GET')

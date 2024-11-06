import logging
import json
from urllib.parse import urljoin
import requests

from django.conf import settings

from api.common.exceptions import UnknownResultException
from api.common.exceptions import RequestFailureException
from api.common.exceptions import ConnectionErrorException
from api.common.exceptions import TimeoutErrorException


logger = logging.getLogger(__name__)

class BinanceClient:
    
    client_settings = settings.BINANCE_TRADER_API_REST_CLIENT
    price_check_endpoint = client_settings['C2C_SEARCH_ENDPOINT']

    def __init__(self, base_url, timeout=10):
        """
        Initialize BinanceClient.

        Args:
            base_url (str): Base URL of the Binance API.
            timeout (int, optional): Request timeout in seconds. Defaults to 10 seconds.
        """
        self.base_url = base_url
        self.timeout = timeout
        self._requests_client = requests.Session()
        self.headers = {"Content-Type": "application/json"}

    def _handle_error_response(self, response, url, method_name):
        """
        Handle error responses from the API.

        Args:
            response (requests.Response): API response object.
            url (str): Request URL.
            method_name (str): Name of the method making the request.

        Raises:
            RequestFailureException: For 4xx errors.
            UnknownResultException: For 5xx errors.
        """
        error_message = response.text
        logger.error(
            f'Binance API error in {method_name}: {error_message}',
            extra={
                'url': url,
                'method': method_name,
                'response_status_code': response.status_code,
                'response_body': response.content,
            }
        )
        
        if 400 <= response.status_code < 500:
            raise RequestFailureException(url=url, response=response)
        elif response.status_code >= 500:
            raise UnknownResultException(url=url, response=response)
    
    def make_request(self, http_method, endpoint, headers=None, data=None, expected_http_codes=None, method_name=""):
        """
        Make an HTTP request to the Binance API.

        Args:
            http_method (str): HTTP method (POST).
            endpoint (str): API endpoint.
            headers (dict, optional): Additional headers.
            data (dict, optional): Request data.
            expected_http_codes (list, optional): Expected HTTP codes.
            method_name (str): Name of the method making the request.

        Returns:
            requests.Response: API response.
        """
        url = urljoin(self.base_url, endpoint)
        headers = headers or self.headers
        expected_http_codes = expected_http_codes or [200]

        try:
            response = self._requests_client.request(
                method=http_method,
                url=url,
                headers=headers,
                data=json.dumps(data) if data else None,
                timeout=self.timeout
            )

        except ConnectionErrorException as exc:
            logger.error(
                f'Connection error in {method_name}', 
                exc_info=True, 
                extra={
                    'url': url,
                    'timeout':self.timeout
                }
            )
            raise RequestFailureException(url=url) from exc

        except TimeoutErrorException as exc:
            logger.error(
                f'Timeout in request to the BinanceTrader API in {method_name}',
                exc_info=True,
                extra={
                    'url': url,
                    'timeout_secs': self.timeout,
                },
            )
            raise UnknownResultException(url=url) from exc

        if response.status_code not in expected_http_codes:
            self._handle_error_response(response, url, method_name)

        return response

    
    def get_price(self, **kwargs):
        """
        Gets the current price for a trading pair.
        """
        endpoint = self.price_check_endpoint
        response = self.make_request("POST", endpoint, data=kwargs, method_name='price_check')
        return response
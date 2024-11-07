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
        Initialize BinanceClient with base URL and request timeout.
        """
        self.base_url = base_url
        self.timeout = timeout
        self._requests_client = requests.Session()
        self.headers = {"Content-Type": "application/json"}

    def _handle_error_response(self, response, url, method_name):
        """
        Log and handle API error responses by raising specific exceptions.
        """
        logger.error(
            f'Binance API error in {method_name}: {response.text}',
            extra={
                'url': url,
                'method': method_name,
                'status_code': response.status_code,
                'response_body': response.content,
            }
        )
        if 400 <= response.status_code < 500:
            raise RequestFailureException(url=url, response=response)
        elif response.status_code >= 500:
            raise UnknownResultException(url=url, response=response)
    
    def make_request(self, http_method, endpoint, headers=None, data=None, expected_http_codes=[200], method_name=""):
        """
        Send a request to Binance API and handle potential errors.
        """
        url = urljoin(self.base_url, endpoint)
        headers = headers or self.headers

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
                extra={'url': url,'timeout':self.timeout}
            )
            raise RequestFailureException(url=url) from exc

        except TimeoutErrorException as exc:
            logger.error(
                f'Timeout in request to the BinanceTrader API in {method_name}',
                exc_info=True,
                extra={'url': url,'timeout_secs': self.timeout},
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
        response = self.make_request("POST", endpoint, data=kwargs, method_name='get_price')
        return response
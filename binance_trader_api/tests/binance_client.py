import requests_mock

from django.conf import settings
from django.test import TestCase

from constance import config

from api.common.exceptions import RequestFailureException
from api.common.exceptions import UnknownResultException
from api.common.vcr_helpers import vcr

from ..binance_client import BinanceClient

class BinanceTraderPriceCheckTestCase(TestCase):
    def setUp(self):
        self.test_data = {
            "fiat": "COP",
            "page": 1,
            "rows": 3,
            "transAmount": 100000,
            "tradeType": "BUY",
            "asset": "USDT",
            "countries": [],
            "proMerchantAds": False,
            "shieldMerchantAds": False,
            "filterType": "all",
            "periods": [],
            "additionalKycVerifyFilter": 0,
            "publisherType": "merchant",
            "payTypes": ["BancolombiaSA", "Nequi"],
            "classifies": ["mass", "profession"]
        }
        client_settings = settings.BINANCE_TRADER_API_REST_CLIENT
        self.base_url = client_settings['BASE_URL']
        timeout = config.BINANCE_TRADER_API_REST_CLIENT_TIMEOUT_SECS 

        self.client_binance = BinanceClient(
            base_url = self.base_url,
            timeout = timeout
        )
    
        self.get_price_url = self.base_url + BinanceClient.price_check_endpoint

    @vcr.use_cassette
    def test_successful_price_check(self):
        """Test successful price check request"""

        response = self.client_binance.get_price(**self.test_data)
        json_response = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertIn('data', json_response)

    @requests_mock.Mocker()
    def test_price_check_error_server(self, mocker):

        mocker.post(
            self.get_price_url,
            status_code=500,
            json={'error': 'Internal Server Error'}
        )
        with self.assertRaises(UnknownResultException) as context:
            self.client_binance.get_price(**self.test_data)
        self.assertEqual(context.exception.response.status_code, 500)
        self.assertIn("Internal Server Error", str(context.exception.response.content))
    
    @requests_mock.Mocker()
    def test_price_check_bad_request(self, mocker):

        mocker.post(
            self.get_price_url,
            status_code=400,
            json={'error': 'Bad request'}
        )
        with self.assertRaises(RequestFailureException) as context:
            self.client_binance.get_price(**self.test_data)
        self.assertEqual(context.exception.response.status_code, 400)
        self.assertIn("Bad request", str(context.exception.response.content))
    
    
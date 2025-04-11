from typing import Optional

import requests


class RequestFailureException(Exception):
    """Raised when request fails and no operation was performed on remote side"""

    def __init__(
        self,
        *args,
        url: str = "",
        response: Optional[requests.Response] = None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.url = url
        self.response = response


class UnknownResultException(Exception):
    """Raised when cannot determine if operation succeeded or failed"""

    def __init__(
        self,
        *args,
        url: str = "",
        response: Optional[requests.Response] = None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.url = url
        self.response = response


# Connection errors (safe to retry)
ConnectionErrorException = (
    requests.exceptions.ConnectionError,
    requests.exceptions.ConnectTimeout,
    requests.packages.urllib3.exceptions.ConnectTimeoutError,
)

# Timeout errors (unsafe to retry)
TimeoutErrorException = (
    requests.exceptions.Timeout,
    requests.exceptions.ReadTimeout,
    requests.packages.urllib3.exceptions.ReadTimeoutError,
    requests.exceptions.RequestException,
)

"""
OAMI Enterprise
OpenAlgo REST Client
"""

from typing import Any, Dict

import httpx


class OpenAlgoRESTClient:
    """
    OpenAlgo REST Client
    """

    def __init__(
        self,
        rest_url: str,
        api_key: str,
        timeout: int = 10,
    ):

        self.base_url = rest_url.rstrip("/")
        self.api_key = api_key

        self.client = httpx.Client(
            timeout=timeout
        )

    def get(
        self,
        endpoint: str,
        params: Dict[str, Any] | None = None,
    ):

        headers = {
            "X-API-KEY": self.api_key
        }

        return self.client.get(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=headers,
        )

    def post(
        self,
        endpoint: str,
        data: Dict[str, Any],
    ):

        headers = {
            "X-API-KEY": self.api_key
        }

        return self.client.post(
            f"{self.base_url}{endpoint}",
            json=data,
            headers=headers,
        )
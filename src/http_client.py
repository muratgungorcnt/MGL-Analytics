"""
Asynchronous HTTP client using aiohttp for API requests
"""

import logging
import aiohttp
from typing import Dict, Optional, Any
from src.decorators import async_safe_run
from src.errors import APIError

logger = logging.getLogger(__name__)


class AsyncHTTPClient:
    """
    Asynchronous HTTP client for making API requests.
    Handles retries, timeouts, and rate limiting.
    """

    def __init__(
        self,
        timeout: int = 15,
        max_retries: int = 3,
        ssl_verify: bool = False
    ):
        """
        Initialize HTTP client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            ssl_verify: Whether to verify SSL certificates
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.ssl_verify = ssl_verify
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """
        Async context manager entry.
        """
        connector = aiohttp.TCPConnector(ssl=self.ssl_verify)
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            connector=connector
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit.
        """
        if self.session:
            await self.session.close()

    @async_safe_run(default_return={}, log_level="ERROR", retries=2)
    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make GET request.

        Args:
            url: Request URL
            headers: Optional request headers
            params: Optional query parameters

        Returns:
            JSON response as dictionary

        Raises:
            APIError: If request fails
        """
        if not self.session:
            raise APIError("HTTP session not initialized. Use 'async with' context manager.")

        try:
            async with self.session.get(
                url,
                headers=headers,
                params=params,
                ssl=self.ssl_verify
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise APIError(
                        f"API request failed: {response.status} {await response.text()}"
                    )
        except aiohttp.ClientError as e:
            raise APIError(f"HTTP client error: {str(e)}")

    @async_safe_run(default_return={}, log_level="ERROR", retries=2)
    async def post(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make POST request.

        Args:
            url: Request URL
            json: JSON payload
            headers: Optional request headers

        Returns:
            JSON response as dictionary

        Raises:
            APIError: If request fails
        """
        if not self.session:
            raise APIError("HTTP session not initialized. Use 'async with' context manager.")

        try:
            async with self.session.post(
                url,
                json=json,
                headers=headers,
                ssl=self.ssl_verify
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise APIError(
                        f"API request failed: {response.status} {await response.text()}"
                    )
        except aiohttp.ClientError as e:
            raise APIError(f"HTTP client error: {str(e)}")

    def __repr__(self) -> str:
        return f"AsyncHTTPClient(timeout={self.timeout.total}s, retries={self.max_retries})"

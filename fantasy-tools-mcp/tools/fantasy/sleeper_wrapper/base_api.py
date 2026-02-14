import aiohttp
import requests

from helpers.retry_utils import async_retry_with_backoff, retry_with_backoff


class BaseApi:
    @retry_with_backoff()
    def _call(self, url: str) -> dict:
        result_json_string = requests.get(url)
        result_json_string.raise_for_status()
        result = result_json_string.json()
        return result

    @async_retry_with_backoff()
    async def _call_async(self, url: str) -> dict:
        """
        Async version of _call using aiohttp for parallel API requests.

        Args:
            url: The URL to fetch

        Returns:
            Parsed JSON response as dict

        Raises:
            aiohttp.ClientResponseError: On HTTP error status codes
            aiohttp.ClientError: On connection/timeout errors
        """
        async with aiohttp.ClientSession() as session, session.get(url) as response:
            response.raise_for_status()
            result = await response.json()
            return result

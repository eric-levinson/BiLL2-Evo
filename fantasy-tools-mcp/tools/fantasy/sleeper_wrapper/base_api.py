import requests
import json
from helpers.retry_utils import retry_with_backoff


class BaseApi():
	@retry_with_backoff()
	def _call(self, url: str) -> dict:
		result_json_string = requests.get(url)
		result_json_string.raise_for_status()
		result = result_json_string.json()
		return result
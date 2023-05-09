"""
Contains various condition functions for API request retries.
"""

from typing import Callable

from requests import Response

RetryCondition = Callable[["LinodeClient", Response], bool]


def condition_408(client: "LinodeClient", response: Response) -> bool:
    """
    Allows for retries on 408 responses.
    """
    return response.status_code == 408


def condition_429(client: "LinodeClient", response: Response) -> bool:
    """
    Allows for retries on 429 responses.
    """
    return response.status_code == 429

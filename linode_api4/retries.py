"""
Contains various
"""

from typing import Callable

from requests import Response

RetryCondition = Callable[["LinodeClient", Response], bool]


def condition_408(client: "LinodeClient", response: Response) -> bool:
    return response.status_code == 408


def condition_429(client: "LinodeClient", response: Response) -> bool:
    return response.status_code == 429

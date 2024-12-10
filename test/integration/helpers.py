import random
import time
from string import ascii_lowercase
from typing import Callable

from linode_api4.errors import ApiError


def get_test_label(length: int = 8):
    return "".join(random.choice(ascii_lowercase) for i in range(length))


def wait_for_condition(
    interval: int, timeout: int, condition: Callable, *args
) -> object:
    end_time = time.time() + timeout
    while time.time() < end_time:
        result = condition(*args)
        if result:
            return result
        time.sleep(interval)
    raise TimeoutError(
        f"Timeout Error: resource not available in {timeout} seconds"
    )


# Retry function to help in case of requests sending too quickly before instance is ready
def retry_sending_request(
    retries: int, condition: Callable, *args, backoff: int = 5, **kwargs
) -> object:
    for attempt in range(1, retries + 1):
        try:
            return condition(*args, **kwargs)
        except ApiError:
            if attempt == retries:
                raise ApiError(
                    "Api Error: Failed after all retry attempts"
                ) from None
            time.sleep(backoff)


def send_request_when_resource_available(
    timeout: int, func: Callable, *args, **kwargs
) -> object:
    start_time = time.time()
    retry_statuses = {400, 500}

    while True:
        try:
            return func(*args, **kwargs)
        except ApiError as e:
            if e.status in retry_statuses or "Please try again later" in str(e):
                if time.time() - start_time > timeout:
                    raise TimeoutError(
                        f"Timeout Error: resource not available in {timeout} seconds"
                    )
                time.sleep(10)
            else:
                raise e

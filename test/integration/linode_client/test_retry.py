from test.integration.conftest import get_token

import httpretty
import pytest

from linode_api4 import ApiError, LinodeClient

"""
Tests for retrying on intermittent errors.

.. warning::
   This test class _does not_ follow normal testing conventions for this project,
   as requests are not automatically mocked.  Only add tests to this class if they
   pertain to the retry logic, and make sure you mock the requests calls yourself
   (or else they will make real requests and those won't work).
"""
ERROR_RESPONSES = [
    httpretty.Response(
        body="{}",
        status=408,
    ),
    httpretty.Response(
        body="{}",
        status=429,
    ),
    httpretty.Response(
        body="{}",
        status=200,
    ),
]


def get_retry_client():
    client = LinodeClient(token=get_token(), base_url="https://localhost")
    # sidestep the validation to do immediate retries so tests aren't slow
    client.retry_rate_limit_interval = 0.1
    return client


@pytest.mark.smoke
@httpretty.activate
def test_get_retry_statuses():
    """
    Tests that retries work as expected on 408 and 429 responses.
    """

    httpretty.register_uri(
        httpretty.GET, "https://localhost/test", responses=ERROR_RESPONSES
    )

    get_retry_client().get("/test")

    assert len(httpretty.latest_requests()) == 3


@httpretty.activate
def test_put_retry_statuses():
    """
    Tests that retries work as expected on 408 and 429 responses.
    """

    httpretty.register_uri(
        httpretty.PUT, "https://localhost/test", responses=ERROR_RESPONSES
    )

    get_retry_client().put("/test")

    assert len(httpretty.latest_requests()) == 3


@httpretty.activate
def test_post_retry_statuses():
    httpretty.register_uri(
        httpretty.POST, "https://localhost/test", responses=ERROR_RESPONSES
    )

    get_retry_client().post("/test")

    assert len(httpretty.latest_requests()) == 3


@httpretty.activate
def test_delete_retry_statuses():
    httpretty.register_uri(
        httpretty.DELETE, "https://localhost/test", responses=ERROR_RESPONSES
    )

    get_retry_client().delete("/test")

    assert len(httpretty.latest_requests()) == 3


@httpretty.activate
def test_retry_max():
    """
    Tests that retries work as expected on 408 and 429 responses.
    """

    httpretty.register_uri(
        httpretty.GET,
        "https://localhost/test",
        responses=[
            httpretty.Response(
                body="{}",
                status=408,
            ),
            httpretty.Response(
                body="{}",
                status=429,
            ),
            httpretty.Response(
                body="{}",
                status=429,
            ),
        ],
    )

    client = get_retry_client()
    client.retry_max = 2

    try:
        client.get("/test")
    except ApiError as err:
        assert err.status == 429
    else:
        raise RuntimeError("Expected retry error after exceeding max retries")

    assert len(httpretty.latest_requests()) == 3


@httpretty.activate
def test_retry_disable():
    """
    Tests that retries can be disabled.
    """

    httpretty.register_uri(
        httpretty.GET,
        "https://localhost/test",
        responses=[
            httpretty.Response(
                body="{}",
                status=408,
            ),
        ],
    )

    client = get_retry_client()
    client.retry = False

    try:
        client.get("/test")
    except ApiError as e:
        assert e.status == 408
    else:
        raise RuntimeError("Expected 408 error to be raised")

    assert len(httpretty.latest_requests()) == 1


@httpretty.activate
def test_retry_works_with_integer_interval_value():
    """
    Tests that retries work as expected on 408 and 429 responses.
    """

    httpretty.register_uri(
        httpretty.GET, "https://localhost/test", responses=ERROR_RESPONSES
    )

    client = get_retry_client()
    client.retry_max = 2
    client.retry_rate_limit_interval = 1

    client.get("/test")

    assert len(httpretty.latest_requests()) == 3

import copy
import json

import httpretty
import pytest

from linode_api4 import LinodeClient


@pytest.fixture(scope="module")
def body_event_list_empty():
    return {"data": [], "page": 1, "pages": 1, "results": 0}


@pytest.fixture(scope="module")
def body_event_started(body_event_list_empty):
    body = copy.deepcopy(body_event_list_empty)
    body["data"].append(
        {
            "action": "linode_shutdown",
            "entity": {
                "id": 11111,
                "type": "ticket",
            },
            "id": 123,
            "status": "started",
        }
    )
    body["results"] = 1

    return body


@pytest.fixture(scope="module")
def body_event_finished(body_event_started):
    body = copy.deepcopy(body_event_started)
    body["data"][0]["status"] = "finished"
    return body


@pytest.fixture(scope="module")
def body_event_notification(body_event_started):
    body = copy.deepcopy(body_event_started)
    body["data"][0]["status"] = "notification"
    return body


class TestPolling:
    @pytest.fixture(scope="class")
    def client(self):
        return LinodeClient("testing", base_url="https://localhost")

    @httpretty.activate
    def test_wait_for_entity_free(
        self,
        client,
        body_event_started,
        body_event_finished,
    ):
        """
        Tests that the wait_for_entity_free method works as expected.
        """

        httpretty.register_uri(
            httpretty.GET,
            "https://localhost/account/events",
            responses=[
                httpretty.Response(
                    body=json.dumps(body_event_started),
                    status=200,
                ),
                httpretty.Response(
                    body=json.dumps(body_event_finished),
                    status=200,
                ),
                httpretty.Response(
                    body=json.dumps(body_event_finished),
                    status=200,
                ),
            ],
        )

        client.polling.wait_for_entity_free(
            "linode",
            11111,
            10,
            0.1,
        )

        assert len(httpretty.latest_requests()) == 2

    @httpretty.activate
    def test_wait_for_entity_free_notification(
        self,
        client,
        body_event_notification,
    ):
        """
        Tests that the wait_for_entity_free method works as expected with a notification event.
        """

        httpretty.register_uri(
            httpretty.GET,
            "https://localhost/account/events",
            responses=[
                httpretty.Response(
                    body=json.dumps(body_event_notification),
                    status=200,
                ),
                httpretty.Response(
                    body=json.dumps(body_event_notification),
                    status=200,
                ),
            ],
        )

        client.polling.wait_for_entity_free(
            "linode",
            11111,
            10,
            0.1,
        )

        assert len(httpretty.latest_requests()) == 1

import json

import httpretty
import pytest

from linode_api4 import LinodeClient


class TestPolling:
    @pytest.fixture(scope="class")
    def client(self):
        return LinodeClient("testing", base_url="https://localhost")

    @staticmethod
    def body_event_status(status: str, action: str = "linode_shutdown"):
        return {
            "action": action,
            "entity": {
                "id": 11111,
                "type": "linode",
            },
            "id": 123,
            "status": status,
        }

    @staticmethod
    def body_event_list_empty():
        return {"data": [], "page": 1, "pages": 1, "results": 0}

    @staticmethod
    def body_event_list_status(status: str, action="linode_shutdown"):
        body = TestPolling.body_event_list_empty()
        body["data"].append(
            TestPolling.body_event_status(status, action=action)
        )
        body["results"] = 1

        return body

    @httpretty.activate
    def test_wait_for_entity_free(
        self,
        client,
    ):
        """
        Tests that the wait_for_entity_free method works as expected.
        """

        httpretty.register_uri(
            httpretty.GET,
            "https://localhost/account/events",
            responses=[
                httpretty.Response(
                    body=json.dumps(self.body_event_list_status("started")),
                    status=200,
                ),
                httpretty.Response(
                    body=json.dumps(self.body_event_list_status("finished")),
                    status=200,
                ),
                httpretty.Response(
                    body=json.dumps(self.body_event_list_status("finished")),
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
    ):
        """
        Tests that the wait_for_entity_free method works as expected with a notification event.
        """

        httpretty.register_uri(
            httpretty.GET,
            "https://localhost/account/events",
            responses=[
                httpretty.Response(
                    body=json.dumps(
                        self.body_event_list_status("notification")
                    ),
                    status=200,
                ),
                httpretty.Response(
                    body=json.dumps(
                        self.body_event_list_status("notification")
                    ),
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

        for r in httpretty.latest_requests():
            filter_header = r.headers["X-Filter"]
            assert '"entity.type": "linode"' in filter_header
            assert '"entity.id": 11111' in filter_header

    @httpretty.activate
    def test_wait_for_event_finished(
        self,
        client,
    ):
        """
        Tests that the EventPoller.wait_for_event_finished method works as expected.
        """

        httpretty.register_uri(
            httpretty.GET,
            "https://localhost/account/events/123",
            responses=[
                httpretty.Response(
                    body=json.dumps(self.body_event_status("started")),
                ),
                httpretty.Response(
                    body=json.dumps(self.body_event_status("started")),
                ),
                httpretty.Response(
                    body=json.dumps(self.body_event_status("finished")),
                ),
            ],
        )

        httpretty.register_uri(
            httpretty.GET,
            "https://localhost/account/events",
            responses=[
                httpretty.Response(
                    body=json.dumps(self.body_event_list_empty()),
                    status=200,
                ),
                httpretty.Response(
                    body=json.dumps(self.body_event_list_status("started")),
                    status=200,
                ),
                httpretty.Response(
                    body=json.dumps(self.body_event_list_status("finished")),
                    status=200,
                ),
            ],
        )

        result = client.polling.event_poller_create(
            "linode", "linode_shutdown", entity_id=11111
        ).wait_for_next_event_finished(interval=0.1)

        latest_requests = httpretty.latest_requests()

        list_requests = [
            v for v in latest_requests if v.path == "/account/events"
        ]

        get_requests = [
            v for v in latest_requests if v.path == "/account/events/123"
        ]

        for r in list_requests:
            filter_header = r.headers["X-Filter"]
            assert '"entity.type": "linode"' in filter_header
            assert '"entity.id": 11111' in filter_header

        assert len(list_requests) == 2
        assert len(get_requests) == 3
        assert result.entity.id == 11111
        assert result.status == "finished"

    @httpretty.activate
    def test_wait_for_event_finished_creation(
        self,
        client,
    ):
        """
        Tests that the EventPoller.wait_for_event_finished method
        works as expected on newly created entities.
        """

        action = "linode_create"

        httpretty.register_uri(
            httpretty.GET,
            "https://localhost/account/events/123",
            responses=[
                httpretty.Response(
                    body=json.dumps(
                        self.body_event_status("started", action=action)
                    ),
                ),
                httpretty.Response(
                    body=json.dumps(
                        self.body_event_status("started", action=action)
                    ),
                ),
                httpretty.Response(
                    body=json.dumps(
                        self.body_event_status("finished", action=action)
                    ),
                ),
            ],
        )

        httpretty.register_uri(
            httpretty.GET,
            "https://localhost/account/events",
            responses=[
                httpretty.Response(
                    body=json.dumps(self.body_event_list_empty()),
                    status=200,
                ),
                httpretty.Response(
                    body=json.dumps(
                        self.body_event_list_status("started", action=action)
                    ),
                    status=200,
                ),
                httpretty.Response(
                    body=json.dumps(
                        self.body_event_list_status("finished", action=action)
                    ),
                    status=200,
                ),
            ],
        )

        poller = client.polling.event_poller_create(
            "linode",
            "linode_create",
        )

        # Pretend we created an instance here
        instance_id = 11111

        poller.set_entity_id(instance_id)

        result = poller.wait_for_next_event_finished(interval=0.1)

        latest_requests = httpretty.latest_requests()

        list_requests = [
            v for v in latest_requests if v.path == "/account/events"
        ]

        get_requests = [
            v for v in latest_requests if v.path == "/account/events/123"
        ]

        for r in list_requests:
            filter_header = r.headers["X-Filter"]
            assert '"entity.type": "linode"' in filter_header
            assert '"entity.id": 11111' in filter_header

        assert len(list_requests) == 2
        assert len(get_requests) == 3
        assert result.entity.id == 11111
        assert result.status == "finished"

from test.unit.base import ClientBaseCase, MonitorClientBaseCase

from linode_api4 import PaginatedList
from linode_api4.objects import (
    AggregateFunction,
    AlertChannel,
    AlertDefinition,
    AlertDefinitionChannel,
    AlertDefinitionEntity,
    EntityMetricOptions,
)
from linode_api4.objects.monitor import (
    BasicAuthenticationDetails,
    ChannelDetails,
    CustomHeader,
    DestinationAuthentication,
    EmailDetails,
    WebhookDetails,
)


class MonitorAPITest(MonitorClientBaseCase):
    """
    Tests methods of the Monitor API group
    """

    def test_fetch_metrics(self):
        service_type = "dbaas"
        url = f"/monitor/services/{service_type}/metrics"
        with self.mock_post(url) as mock_post:
            metrics = self.client.metrics.fetch_metrics(
                service_type,
                entity_ids=[13217, 13316],
                metrics=[
                    EntityMetricOptions(
                        name="avg_read_iops",
                        aggregate_function=AggregateFunction("avg"),
                    ),
                    {"name": "avg_cpu_usage", "aggregate_function": "avg"},
                ],
                relative_time_duration={"unit": "hr", "value": 1},
            )

            # assert call data
            assert mock_post.call_url == url
            assert mock_post.call_data == {
                "entity_ids": [13217, 13316],
                "metrics": [
                    {"name": "avg_read_iops", "aggregate_function": "avg"},
                    {"name": "avg_cpu_usage", "aggregate_function": "avg"},
                ],
                "relative_time_duration": {"unit": "hr", "value": 1},
            }

            # assert the metrics data
            metric_data = metrics.data.result[0]

            assert metrics.data.resultType == "matrix"
            assert metric_data.metric["entity_id"] == 13316
            assert metric_data.metric["metric_name"] == "avg_read_iops"
            assert metric_data.metric["node_id"] == "primary-9"
            assert metric_data.values[0][0] == 1728996500
            assert metric_data.values[0][1] == "90.55555555555556"

            assert metrics.status == "success"
            assert metrics.stats.executionTimeMsec == 21
            assert metrics.stats.seriesFetched == "2"
            assert not metrics.isPartial


class MonitorAlertDefinitionsTest(ClientBaseCase):
    def test_alert_definition(self):
        service_type = "dbaas"
        url = f"/monitor/services/{service_type}/alert-definitions"
        with self.mock_get(url) as mock_get:
            alert = self.client.monitor.alert_definitions(
                service_type=service_type
            )

            assert mock_get.call_url == url

            # assert collection and element types
            assert isinstance(alert, PaginatedList)
            assert isinstance(alert[0], AlertDefinition)
            assert alert[0].scope == "entity"
            assert alert[0].regions == []
            assert alert[0].group_by == ["entity_id"]
            assert alert[0].entities.url.endswith(
                "/alert-definitions/12345/entities"
            )
            assert alert[0].entities.count == 1
            assert alert[0].entities.has_more_resources is False
            assert isinstance(alert[0].alert_channels, list)
            assert len(alert[0].alert_channels) == 1
            assert isinstance(
                alert[0].alert_channels[0], AlertDefinitionChannel
            )
            assert alert[0].alert_channels[0].id == 10000
            assert alert[0].alert_channels[0]._type == "email"

            # fetch the raw JSON from the client and assert its fields
            raw = self.client.get(url)
            # raw is a paginated response; check first item's fields
            first = raw["data"][0]
            assert first["label"] == "Test Alert for DBAAS"
            assert first["service_type"] == "dbaas"
            assert first["status"] == "enabled"
            assert first["group_by"] == ["entity_id"]
            assert first["created"] == "2024-01-01T00:00:00"

    def test_create_alert_definition(self):
        service_type = "dbaas"
        url = f"/monitor/services/{service_type}/alert-definitions"
        result = {
            "id": 67890,
            "label": "Created Alert",
            "service_type": service_type,
            "severity": 1,
            "status": "active",
            "group_by": ["entity_id"],
            "entities": {
                "url": f"/monitor/services/dbaas/alert-definitions/67890/entities",
                "count": 1,
                "has_more_resources": False,
            },
        }

        with self.mock_post(result) as mock_post:
            alert = self.client.monitor.create_alert_definition(
                service_type=service_type,
                label="Created Alert",
                severity=1,
                channel_ids=[1, 2],
                rule_criteria={"rules": []},
                trigger_conditions={"criteria_condition": "ALL"},
                scope="entity",
                regions=[],
                entity_ids=["13217"],
                description="created via test",
                group_by=["entity_id"],
            )

            assert mock_post.call_url == url
            # payload should include the provided fields
            assert mock_post.call_data["label"] == "Created Alert"
            assert mock_post.call_data["severity"] == 1
            assert "channel_ids" in mock_post.call_data
            assert mock_post.call_data["scope"] == "entity"
            assert mock_post.call_data["regions"] == []
            assert mock_post.call_data["group_by"] == ["entity_id"]

            assert isinstance(alert, AlertDefinition)
            assert alert.id == 67890
            assert alert.entities.url.endswith(
                "/alert-definitions/67890/entities"
            )
            assert alert.entities.count == 1
            assert alert.entities.has_more_resources is False
            assert alert.group_by == ["entity_id"]

            # fetch the same response from the client and assert
            resp = self.client.post(url, data={})
            assert resp["label"] == "Created Alert"

    def test_alert_definition_entities(self):
        service_type = "dbaas"
        id = 12345
        url = (
            f"/monitor/services/{service_type}/alert-definitions/{id}/entities"
        )

        with self.mock_get(url) as mock_get:
            entities = self.client.monitor.alert_definition_entities(
                service_type, id
            )

            assert mock_get.call_url == url
            assert isinstance(entities, PaginatedList)
            assert len(entities) == 3

            assert isinstance(entities[0], AlertDefinitionEntity)
            assert entities[0].id == "1"
            assert entities[0].label == "mydatabase-1"
            assert entities[0].url == "/v4/databases/mysql/instances/1"
            assert entities[0]._type == "dbaas"

            assert isinstance(entities[1], AlertDefinitionEntity)
            assert entities[1].id == "2"
            assert entities[1].label == "mydatabase-2"
            assert entities[1].url == "/v4/databases/mysql/instances/2"
            assert entities[1]._type == "dbaas"

            assert isinstance(entities[2], AlertDefinitionEntity)
            assert entities[2].id == "3"
            assert entities[2].label == "mydatabase-3"
            assert entities[2].url == "/v4/databases/mysql/instances/3"
            assert entities[2]._type == "dbaas"

    def test_clone_alert_definition(self):
        service_type = "dbaas"
        source_id = 12345
        url = (
            f"/monitor/services/{service_type}/alert-definitions/"
            f"{source_id}/clone"
        )

        with self.mock_post(url) as mock_post:
            alert = self.client.monitor.clone_alert_definition(
                service_type=service_type,
                id=source_id,
                label="Cloned Alert",
            )

            assert mock_post.call_url == url
            assert mock_post.call_data == {"label": "Cloned Alert"}

            assert isinstance(alert, AlertDefinition)
            assert alert.id == 67891
            assert alert.label == "Cloned Alert"
            assert alert.scope == "entity"
            assert alert.group_by == ["entity_id"]
            assert alert.rule_criteria is not None
            assert alert.entities.url.endswith(
                "/alert-definitions/67891/entities"
            )

            # fetch the same response from the client and assert
            resp = self.client.post(url, data={})
            assert resp["label"] == "Cloned Alert"

    def test_clone_alert_definition_with_optional_fields(self):
        service_type = "dbaas"
        source_id = 12345
        url = (
            f"/monitor/services/{service_type}/alert-definitions/"
            f"{source_id}/clone"
        )

        with self.mock_post(url) as mock_post:
            self.client.monitor.clone_alert_definition(
                service_type=service_type,
                id=source_id,
                label="Cloned Alert",
                description="cloned via test",
                scope="entity",  # same as source alert definition
                regions=[],
                entity_ids=["13217"],
                severity=1,
                rule_criteria={"rules": []},
                trigger_conditions={"criteria_condition": "ALL"},
                channel_ids=[1, 2],
                group_by=["entity_id"],
            )

            assert mock_post.call_url == url
            assert mock_post.call_data["label"] == "Cloned Alert"
            assert mock_post.call_data["description"] == "cloned via test"
            assert mock_post.call_data["scope"] == "entity"
            assert mock_post.call_data["regions"] == []
            assert mock_post.call_data["entity_ids"] == ["13217"]
            assert mock_post.call_data["severity"] == 1
            assert mock_post.call_data["rule_criteria"] == {"rules": []}
            assert mock_post.call_data["trigger_conditions"] == {
                "criteria_condition": "ALL"
            }
            assert mock_post.call_data["channel_ids"] == [1, 2]
            assert mock_post.call_data["group_by"] == ["entity_id"]

    def test_create_email_channel(self):
        """
        Test creating an email alert channel.
        Verifies that channel_create() properly handles email channel details.
        """
        create_url = "/monitor/alert-channels"
        channel_id = 789
        channel_url = f"{create_url}/{channel_id}"

        create_response = {
            "id": channel_id,
            "label": "Email Test Channel",
            "type": "user",
            "channel_type": "email",
            "details": {
                "email": {
                    "usernames": ["test_user1", "test_user2"],
                    "recipient_type": "user",
                }
            },
            "alerts": {
                "url": f"{channel_url}/alerts",
                "type": "alerts-definitions",
                "alert_count": 0,
            },
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "created_by": "test_user1",
            "updated_by": "test_user1",
        }

        with self.mock_post(create_response) as mock_post:
            channel = self.client.monitor.channel_create(
                label="Email Test Channel",
                channel_type="email",
                details=ChannelDetails(
                    email=EmailDetails(
                        recipient_type="user",
                        usernames=["test_user1", "test_user2"],
                    )
                ),
            )
            assert mock_post.call_url == create_url
            assert isinstance(channel, AlertChannel)
            assert channel.id == channel_id
            assert channel.label == "Email Test Channel"
            assert channel.channel_type == "email"

    def test_create_webhook_channel(self):
        """
        Test creating a webhook alert channel.
        Verifies that channel_create() properly handles webhook channel details
        with authentication, compression, and custom headers.
        """
        create_url = "/monitor/alert-channels"
        channel_id = 888
        channel_url = f"{create_url}/{channel_id}"

        create_response = {
            "id": channel_id,
            "label": "Webhook Test Channel",
            "type": "user",
            "channel_type": "webhook",
            "details": {
                "webhook": {
                    "endpoint_url": "https://example.com/webhook",
                    "authentication": {
                        "type": "basic",
                        "details": {
                            "basic_authentication_user": "testuser",
                            "basic_authentication_password": "testpass",
                        },
                    },
                    "data_compression": "gzip",
                    "custom_headers": [
                        {"name": "X-API-Key", "value": "secret123"}
                    ],
                }
            },
            "alerts": {
                "url": f"{channel_url}/alerts",
                "type": "alerts-definitions",
                "alert_count": 0,
            },
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "created_by": "webhook_user",
            "updated_by": "webhook_user",
        }

        with self.mock_post(create_response) as mock_post:
            webhook_channel = self.client.monitor.channel_create(
                label="Webhook Test Channel",
                channel_type="webhook",
                details=ChannelDetails(
                    webhook=WebhookDetails(
                        endpoint_url="https://example.com/webhook",
                        authentication=DestinationAuthentication(
                            type="basic",
                            details=BasicAuthenticationDetails(
                                basic_authentication_user="testuser",
                                basic_authentication_password="testpass",
                            ),
                        ),
                        data_compression="gzip",
                        custom_headers=[
                            CustomHeader(name="X-API-Key", value="secret123")
                        ],
                    )
                ),
            )
            assert mock_post.call_url == create_url
            assert isinstance(webhook_channel, AlertChannel)
            assert webhook_channel.id == channel_id
            assert webhook_channel.label == "Webhook Test Channel"
            assert webhook_channel.channel_type == "webhook"
            assert (
                webhook_channel.details.webhook.endpoint_url
                == "https://example.com/webhook"
            )
            assert (
                webhook_channel.details.webhook.authentication.type == "basic"
            )

    def test_verify_webhook_channel(self):
        """
        Test verifying a webhook channel configuration.
        Verifies that verify_webhook() returns success for valid webhook config.
        """
        verify_url = "/monitor/alert-channels/verify"
        verify_response = {"success": True}

        with self.mock_post(verify_response) as mock_verify:
            is_valid = self.client.monitor.verify_webhook(
                WebhookDetails(
                    endpoint_url="https://example.com/webhook",
                    authentication=DestinationAuthentication(
                        type="basic",
                        details=BasicAuthenticationDetails(
                            basic_authentication_user="testuser",
                            basic_authentication_password="testpass",
                        ),
                    ),
                )
            )
            assert mock_verify.call_url == verify_url
            assert is_valid is True

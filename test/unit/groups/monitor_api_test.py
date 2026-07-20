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
from linode_api4.objects.monitor import ChannelDetails, EmailDetails


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
            assert first["status"] == "active"
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
            )

            assert mock_post.call_url == url
            # payload should include the provided fields
            assert mock_post.call_data["label"] == "Created Alert"
            assert mock_post.call_data["severity"] == 1
            assert "channel_ids" in mock_post.call_data
            assert mock_post.call_data["scope"] == "entity"
            assert mock_post.call_data["regions"] == []

            assert isinstance(alert, AlertDefinition)
            assert alert.id == 67890
            assert alert.entities.url.endswith(
                "/alert-definitions/67890/entities"
            )
            assert alert.entities.count == 1
            assert alert.entities.has_more_resources is False

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

    def test_create_update_delete_alert_channel(self):
        """
        E2E test for alert channel CRUD: create, update, and delete.
        Verifies the full lifecycle of an alert channel.
        """
        create_url = "/monitor/alert-channels"
        channel_id = 789
        channel_url = f"{create_url}/{channel_id}"

        # Create channel
        create_response = {
            "id": channel_id,
            "label": "Test Channel",
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
                label="Test Channel",
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
            assert channel.label == "Test Channel"

        # Update channel
        updated_response = create_response.copy()
        updated_response["label"] = "Test Channel Updated"
        updated_response["updated"] = "2024-01-02T00:00:00"

        with self.mock_put(updated_response) as mock_put:
            channel.label = "Test Channel Updated"
            result = channel.save()

            assert mock_put.call_url == channel_url
            assert result is True
            assert channel.label == "Test Channel Updated"

        # Delete channel
        with self.mock_delete() as mock_delete:
            result = channel.delete()

            assert mock_delete.call_url == channel_url
            assert result is True

    def test_alert_channel(self):
        """
        Test retrieval of a specific alert channel by ID.
        Verifies the alert_channel method returns a single AlertChannel object.
        """
        channel_id = 123
        channel_url = f"/monitor/alert-channels/{channel_id}"

        channel_response = {
            "id": channel_id,
            "label": "alert notification channel",
            "type": "user",
            "channel_type": "email",
            "details": {
                "email": {
                    "usernames": ["admin-user1", "admin-user2"],
                    "recipient_type": "user",
                }
            },
            "alerts": {
                "url": f"{channel_url}/alerts",
                "type": "alerts-definitions",
                "alert_count": 2,
            },
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "created_by": "tester",
            "updated_by": "tester",
        }

        with self.mock_get(channel_response) as mock_get:
            channel = self.client.monitor.alert_channel(channel_id=channel_id)

            assert mock_get.call_url == channel_url
            assert isinstance(channel, AlertChannel)
            assert channel.id == channel_id
            assert channel.label == "alert notification channel"
            assert channel.channel_type == "email"
            assert channel.details.email.usernames == [
                "admin-user1",
                "admin-user2",
            ]
            assert channel.alerts.alert_count == 2

    def test_alert_channel_alerts(self):
        """
        Test retrieval of alerts associated with a specific alert channel.
        Verifies the alert_channel_alerts method returns a paginated list
        of AlertDefinition objects associated with the channel.
        """
        channel_id = 123
        alerts_url = f"/monitor/alert-channels/{channel_id}/alerts"

        alerts_response = {
            "data": [
                {
                    "id": 12345,
                    "label": "DBAAS Alert 1",
                    "service_type": "dbaas",
                    "type": "alerts-definitions",
                    "url": "/monitor/services/dbaas/alerts-definitions/12345",
                },
                {
                    "id": 12346,
                    "label": "DBAAS Alert 2",
                    "service_type": "dbaas",
                    "type": "alerts-definitions",
                    "url": "/monitor/services/dbaas/alerts-definitions/12346",
                },
            ],
            "page": 1,
            "pages": 1,
            "results": 2,
        }

        with self.mock_get(alerts_response) as mock_get:
            alerts = self.client.monitor.alert_channel_alerts(
                channel_id=channel_id
            )

            assert mock_get.call_url == alerts_url
            assert isinstance(alerts, PaginatedList)
            assert len(alerts) == 2

            # Verify first alert
            assert isinstance(alerts[0], AlertDefinition)
            assert alerts[0].id == 12345
            assert alerts[0].label == "DBAAS Alert 1"
            assert alerts[0].service_type == "dbaas"

            # Verify second alert
            assert isinstance(alerts[1], AlertDefinition)
            assert alerts[1].id == 12346
            assert alerts[1].label == "DBAAS Alert 2"
            assert alerts[1].service_type == "dbaas"

from test.unit.base import ClientBaseCase, MonitorClientBaseCase

from linode_api4 import PaginatedList
from linode_api4.objects import (
    AggregateFunction,
    AlertDefinition,
    EntityMetricOptions,
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
            "severity": "warning",
            "status": "active",
        }

        with self.mock_post(result) as mock_post:
            alert = self.client.monitor.create_alert_definition(
                service_type=service_type,
                label="Created Alert",
                severity=1,
                channel_ids=[1, 2],
                rule_criteria={"rules": []},
                trigger_conditions={"criteria_condition": "ALL"},
                entity_ids=["13217"],
                description="created via test",
            )

            assert mock_post.call_url == url
            # payload should include the provided fields
            assert mock_post.call_data["label"] == "Created Alert"
            assert mock_post.call_data["severity"] == "warning"
            assert "channel_ids" in mock_post.call_data

            assert isinstance(alert, AlertDefinition)
            assert alert.id == 67890

            # fetch the same response from the client and assert
            resp = self.client.post(url, data={})
            assert resp["label"] == "Created Alert"

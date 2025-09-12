from linode_api4.objects import (
    AggregateFunction,
    AlertDefinition,
    EntityMetricOptions,
)

from test.unit.base import MonitorClientBaseCase


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

class MonitorAlertDefinitionsTest(MonitorClientBaseCase):
    def test_get_alert_definition(self):
        service_type = "dbaas"
        alert_id = 12345
        url = f"/monitor/services/{service_type}/alert-definitions/{alert_id}"
        with self.mock_get(url) as mock_get:
            alert = self.client.monitor.get_alert_definitions(
                service_type=service_type, alert_id=alert_id
            )

            # assert call
            assert mock_get.call_url == url

            # assert object
            assert isinstance(alert, AlertDefinition)
            assert alert.id == 12345

            # fetch the raw JSON from the client and assert its fields
            raw = self.client.get(url)
            assert raw["label"] == "Test Alert for DBAAS"
            assert raw["service_type"] == "dbaas"
            assert raw["status"] == "active"
            assert raw["created"] == "2024-01-01T00:00:00"

    def test_alert_definitions_requires_service_type_when_id_given(self):
        # alert_id without service_type should raise ValueError
        try:
            self.client.monitor.get_alert_definitions(alert_id=12345)
            raised = False
        except ValueError:
            raised = True
        assert raised

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
                severity="warning",
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

    def test_update_alert_definition(self):
        service_type = "dbaas"
        alert_id = 12345
        url = f"/monitor/services/{service_type}/alert-definitions/{alert_id}"
        result = {"id": alert_id, "label": "Updated Label"}

        with self.mock_put(result) as mock_put:
            alert = self.client.monitor.update_alert_definition(
                service_type=service_type, alert_id=alert_id, label="Updated Label"
            )

            assert mock_put.call_url == url
            assert mock_put.call_data["label"] == "Updated Label"

            assert isinstance(alert, AlertDefinition)
            assert alert.id == alert_id

            resp = self.client.put(url, data={})
            assert resp["label"] == "Updated Label"

    def test_delete_alert_definition(self):
        service_type = "dbaas"
        alert_id = 12345
        url = f"/monitor/services/{service_type}/alert-definitions/{alert_id}"

        with self.mock_delete() as mock_delete:
            self.client.monitor.delete_alert_definition(service_type, alert_id)

            assert mock_delete.call_url == url
            assert mock_delete.called

from test.unit.base import MonitorClientBaseCase

from linode_api4.objects import AggregateFunction, EntityMetricOptions


class MonitorAPITest(MonitorClientBaseCase):
    """
    Tests methods of the Monitor API group
    """

    def test_fetch_metrics(self):
        service_type = "dbaas"
        url = f"/monitor/services/{service_type}/metrics"
        with self.mock_post(url) as m:
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
            assert m.call_url == url
            assert m.call_data == {
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
    """
    Tests alert_definitions method of the Monitor group
    """

    def test_alert_definitions_list_all_calls_endpoint(self):
        url = "/monitor/alert-definitions"
        with self.mock_get(url) as m:
            alerts = self.client.monitor.alert_definitions()

            # assert the correct endpoint was called
            assert m.call_url == url

            # force evaluation of the paginated list (if applicable)
            alerts_list = list(alerts)
            assert isinstance(alerts_list, list)
            if alerts_list:
                first = alerts_list[0]
                # basic shape assertions
                assert hasattr(first, "id")
                assert hasattr(first, "label")
                assert hasattr(first, "service_type")

    def test_alert_definitions_for_service_calls_endpoint(self):
        service_type = "dbaas"
        url = f"/monitor/services/{service_type}/alert-definitions"
        with self.mock_get(url) as m:
            alerts = self.client.monitor.alert_definitions(service_type=service_type)

            # assert the correct endpoint was called
            assert m.call_url == url

            # inspect the returned iterable
            alerts_list = list(alerts)
            assert isinstance(alerts_list, list)

    def test_alert_definition_single_returns_object(self):
        service_type = "dbaas"
        alert_id = 12345
        url = f"/monitor/services/{service_type}/alert-definitions/{alert_id}"
        with self.mock_get(url) as m:
            single = self.client.monitor.alert_definitions(
                service_type=service_type, alert_id=alert_id
            )

            # assert the correct endpoint was called
            assert m.call_url == url

            # returned object should represent a single alert definition
            assert hasattr(single, "id")
            assert single.id == alert_id
            assert hasattr(single, "label")
            assert hasattr(single, "service_type")
            # service_type should match requested service_type when present in response
            if hasattr(single, "service_type") and single.service_type is not None:
                assert single.service_type == service_type

    def test_alert_definitions_requires_service_when_alert_id_provided(self):
        # alert_id without service_type should raise ValueError
        try:
            self.client.monitor.alert_definitions(alert_id=1)
            raised = False
        except ValueError:
            raised = True
        assert raised
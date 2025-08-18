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

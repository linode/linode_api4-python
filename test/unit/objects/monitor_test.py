import datetime
from test.unit.base import ClientBaseCase

from linode_api4.objects import MonitorDashboard, MonitorService


class MonitorTest(ClientBaseCase):
    """
    Tests the methods of MonitorServiceSupported class
    """

    def test_supported_services(self):
        """
        Test the services supported by monitor
        """
        service = self.client.monitor.services()
        self.assertEqual(len(service), 1)
        self.assertEqual(service[0].label, "Databases")
        self.assertEqual(service[0].service_type, "dbaas")

    def test_dashboard_by_ID(self):
        """
        Test the dashboard by ID API
        """
        dashboard = self.client.load(MonitorDashboard, 1)
        self.assertEqual(dashboard.type, "standard")
        self.assertEqual(
            dashboard.created, datetime.datetime(2024, 10, 10, 5, 1, 58)
        )
        self.assertEqual(dashboard.id, 1)
        self.assertEqual(dashboard.label, "Resource Usage")
        self.assertEqual(dashboard.service_type, "dbaas")
        self.assertEqual(
            dashboard.updated, datetime.datetime(2024, 10, 10, 5, 1, 58)
        )
        self.assertEqual(dashboard.widgets[0].aggregate_function, "sum")
        self.assertEqual(dashboard.widgets[0].chart_type, "area")
        self.assertEqual(dashboard.widgets[0].color, "default")
        self.assertEqual(dashboard.widgets[0].label, "CPU Usage")
        self.assertEqual(dashboard.widgets[0].metric, "cpu_usage")
        self.assertEqual(dashboard.widgets[0].size, 12)
        self.assertEqual(dashboard.widgets[0].unit, "%")
        self.assertEqual(dashboard.widgets[0].y_label, "cpu_usage")

    def test_dashboard_by_service_type(self):
        dashboards = self.client.monitor.dashboards(service_type="dbaas")
        self.assertEqual(dashboards[0].type, "standard")
        self.assertEqual(
            dashboards[0].created, datetime.datetime(2024, 10, 10, 5, 1, 58)
        )
        self.assertEqual(dashboards[0].id, 1)
        self.assertEqual(dashboards[0].label, "Resource Usage")
        self.assertEqual(dashboards[0].service_type, "dbaas")
        self.assertEqual(
            dashboards[0].updated, datetime.datetime(2024, 10, 10, 5, 1, 58)
        )
        self.assertEqual(dashboards[0].widgets[0].aggregate_function, "sum")
        self.assertEqual(dashboards[0].widgets[0].chart_type, "area")
        self.assertEqual(dashboards[0].widgets[0].color, "default")
        self.assertEqual(dashboards[0].widgets[0].label, "CPU Usage")
        self.assertEqual(dashboards[0].widgets[0].metric, "cpu_usage")
        self.assertEqual(dashboards[0].widgets[0].size, 12)
        self.assertEqual(dashboards[0].widgets[0].unit, "%")
        self.assertEqual(dashboards[0].widgets[0].y_label, "cpu_usage")

    def test_get_all_dashboards(self):
        dashboards = self.client.monitor.dashboards()
        self.assertEqual(dashboards[0].type, "standard")
        self.assertEqual(
            dashboards[0].created, datetime.datetime(2024, 10, 10, 5, 1, 58)
        )
        self.assertEqual(dashboards[0].id, 1)
        self.assertEqual(dashboards[0].label, "Resource Usage")
        self.assertEqual(dashboards[0].service_type, "dbaas")
        self.assertEqual(
            dashboards[0].updated, datetime.datetime(2024, 10, 10, 5, 1, 58)
        )
        self.assertEqual(dashboards[0].widgets[0].aggregate_function, "sum")
        self.assertEqual(dashboards[0].widgets[0].chart_type, "area")
        self.assertEqual(dashboards[0].widgets[0].color, "default")
        self.assertEqual(dashboards[0].widgets[0].label, "CPU Usage")
        self.assertEqual(dashboards[0].widgets[0].metric, "cpu_usage")
        self.assertEqual(dashboards[0].widgets[0].size, 12)
        self.assertEqual(dashboards[0].widgets[0].unit, "%")
        self.assertEqual(dashboards[0].widgets[0].y_label, "cpu_usage")

    def test_specific_service_details(self):
        data = self.client.load(MonitorService, "dbaas")
        self.assertEqual(data.label, "Databases")
        self.assertEqual(data.service_type, "dbaas")

    def test_metric_definitions(self):

        metrics = self.client.monitor.metric_definitions(service_type="dbaas")
        self.assertEqual(
            metrics[0].available_aggregate_functions,
            ["max", "avg", "min", "sum"],
        )
        self.assertEqual(metrics[0].is_alertable, True)
        self.assertEqual(metrics[0].label, "CPU Usage")
        self.assertEqual(metrics[0].metric, "cpu_usage")
        self.assertEqual(metrics[0].metric_type, "gauge")
        self.assertEqual(metrics[0].scrape_interval, "60s")
        self.assertEqual(metrics[0].unit, "percent")
        self.assertEqual(metrics[0].dimensions[0].dimension_label, "node_type")
        self.assertEqual(metrics[0].dimensions[0].label, "Node Type")
        self.assertEqual(
            metrics[0].dimensions[0].values, ["primary", "secondary"]
        )

    def test_create_token(self):

        with self.mock_post("/monitor/services/dbaas/token") as m:
            self.client.monitor.create_token(
                service_type="dbaas", entity_ids=[189690, 188020]
            )
            self.assertEqual(m.return_dct["token"], "abcdefhjigkfghh")

        with self.mock_post("/monitor/services/linode/token") as m:
            self.client.monitor.create_token(
                service_type="linode", entity_ids=["compute-instance-1"]
            )
            self.assertEqual(m.return_dct["token"], "abcdefhjigkfghh")

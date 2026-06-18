import datetime
from test.unit.base import ClientBaseCase

from linode_api4.objects import AlertChannel, MonitorDashboard, MonitorService
from linode_api4.objects.monitor import ChannelDetails, EmailDetails


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
        self.assertEqual(dashboard.widgets[0].group_by, ["entity_id"])
        self.assertIsNone(dashboard.widgets[0].filters)

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
        self.assertEqual(dashboards[0].widgets[0].group_by, ["entity_id"])
        self.assertIsNone(dashboards[0].widgets[0].filters)

        # Test the second widget which has filters
        self.assertEqual(dashboards[0].widgets[1].label, "Memory Usage")
        self.assertEqual(dashboards[0].widgets[1].group_by, ["entity_id"])
        self.assertIsNotNone(dashboards[0].widgets[1].filters)
        self.assertEqual(len(dashboards[0].widgets[1].filters), 1)
        self.assertEqual(
            dashboards[0].widgets[1].filters[0].dimension_label, "pattern"
        )
        self.assertEqual(dashboards[0].widgets[1].filters[0].operator, "in")
        self.assertEqual(
            dashboards[0].widgets[1].filters[0].value, "publicout,privateout"
        )

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
        self.assertEqual(dashboards[0].widgets[0].group_by, ["entity_id"])
        self.assertIsNone(dashboards[0].widgets[0].filters)

    def test_specific_service_details(self):
        data = self.client.load(MonitorService, "dbaas")
        self.assertEqual(data.label, "Databases")
        self.assertEqual(data.service_type, "dbaas")

        # Test alert configuration
        self.assertIsNotNone(data.alert)
        self.assertEqual(data.alert.polling_interval_seconds, [300])
        self.assertEqual(data.alert.evaluation_period_seconds, [300])
        self.assertEqual(data.alert.scope, ["entity"])

    def test_metric_definitions(self):

        metrics = self.client.monitor.metric_definitions(service_type="dbaas")
        self.assertEqual(
            metrics[0].available_aggregate_functions,
            ["max", "avg", "min", "sum"],
        )
        self.assertTrue(metrics[0].is_alertable)
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

    def test_alert_channels(self):
        channels = self.client.monitor.alert_channels()

        self.assertEqual(len(channels), 1)
        self.assertIsInstance(channels[0], AlertChannel)
        self.assertEqual(channels[0].id, 123)
        self.assertEqual(channels[0].label, "alert notification channel")
        self.assertEqual(channels[0].type, "user")
        self.assertEqual(channels[0].channel_type, "email")
        self.assertIsNotNone(channels[0].details)
        self.assertIsNotNone(channels[0].details.email)
        self.assertEqual(
            channels[0].details.email.usernames,
            ["admin-user1", "admin-user2"],
        )
        self.assertEqual(channels[0].details.email.recipient_type, "user")
        self.assertIsNotNone(channels[0].alerts)
        self.assertEqual(
            channels[0].alerts.url,
            "/monitor/alert-channels/123/alerts",
        )
        self.assertEqual(channels[0].alerts.alert_count, 0)

    def test_create_channel(self):
        
        create_response = {
            "id": 456,
            "label": "Email channel for api change",
            "type": "user",
            "channel_type": "email",
            "details": {
                "email": {
                    "recipient_type": "user",
                    "usernames": ["mawasthy_tenant02_admin"],
                }
            },
            "alerts": {
                "url": "/monitor/alert-channels/456/alerts",
                "type": "alerts-definitions",
                "alert_count": 0,
            },
            "created": "2024-01-01T00:00:00",
            "updated": "2024-01-01T00:00:00",
            "created_by": "mawasthy_tenant02_admin",
            "updated_by": "mawasthy_tenant02_admin",
        }

        with self.mock_post(create_response) as m:
            result = self.client.monitor.channel_create(
                label="Email channel for api change",
                channel_type="email",
                details=ChannelDetails(
                    email=EmailDetails(
                        recipient_type="user",
                        usernames=["mawasthy_tenant02_admin"],
                    )
                ),
            )

        self.assertEqual(m.call_url, "/monitor/alert-channels")
        self.assertEqual(m.call_data["label"], "Email channel for api change")
        self.assertEqual(m.call_data["channel_type"], "email")
        self.assertEqual(
            m.call_data["details"]["email"]["recipient_type"], "user"
        )
        self.assertEqual(
            m.call_data["details"]["email"]["usernames"], ["mawasthy_tenant02_admin"]
        )

        self.assertIsInstance(result, AlertChannel)
        self.assertEqual(result.id, 456)
        self.assertEqual(result.label, "Email channel for api change")
        self.assertEqual(result.type, "user")
        self.assertEqual(result.channel_type, "email")
        self.assertIsNotNone(result.details)
        self.assertIsNotNone(result.details.email)
        self.assertEqual(result.details.email.recipient_type, "user")
        self.assertEqual(result.details.email.usernames, ["mawasthy_tenant02_admin"])

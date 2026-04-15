import datetime
from test.unit.base import ClientBaseCase

from linode_api4.objects import AlertChannel, MonitorDashboard, MonitorService, LogsDestination


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

class LogsDestinationTest(ClientBaseCase):
    """
    Tests methods for LogsDestination class
    """

    def test_list_destinations(self):
        """
        Test that listing destinations returns LogsDestination objects with all fields populated.
        """
        destinations = self.client.monitor.destinations()

        self.assertEqual(len(destinations), 1)
        dest = destinations[0]
        self.assertIsInstance(dest, LogsDestination)
        self.assertEqual(dest.id, 1)
        self.assertEqual(dest.label, "my-logs-destination")
        self.assertEqual(dest.type, "akamai_object_storage")
        self.assertEqual(dest.status, "active")
        self.assertEqual(dest.version, 1)
        self.assertEqual(
            dest.created, datetime.datetime(2024, 6, 1, 12, 0, 0)
        )
        self.assertEqual(
            dest.updated, datetime.datetime(2024, 6, 1, 12, 0, 0)
        )
        self.assertEqual(dest.created_by, "tester")
        self.assertEqual(dest.updated_by, "tester")

    def test_list_destinations_details(self):
        """
        Test that the nested LogsDestinationDetails are deserialized correctly.
        """
        dest = self.client.load(LogsDestination, 1)

        self.assertIsNotNone(dest.details)
        self.assertEqual(dest.details.access_key_id, "1ABCD23EFG4HIJKLMNO5")
        self.assertEqual(dest.details.bucket_name, "primary-bucket")
        self.assertEqual(
            dest.details.host, "primary-bucket.us-east-1.linodeobjects.com"
        )
        self.assertEqual(dest.details.path, "audit-logs")

        self.assertIsNone(dest.details.access_key_secret)

    def test_destination_history(self):
        """
        Test that the history property returns LogsDestinationHistory objects.
        """
        dest = self.client.load(LogsDestination, 1)
        history = dest.history

        self.assertEqual(len(history), 1)
        snapshot = history[0]
        self.assertEqual(snapshot.id, 1)
        self.assertEqual(snapshot.label, "my-logs-destination")
        self.assertEqual(snapshot.type, "akamai_object_storage")
        self.assertEqual(snapshot.status, "active")
        self.assertEqual(snapshot.version, 2)
        self.assertEqual(
            snapshot.updated, datetime.datetime(2024, 6, 2, 9, 0, 0)
        )
        self.assertIsNotNone(snapshot.details)
        self.assertEqual(snapshot.details.bucket_name, "primary-bucket")

    def test_create_destination(self):
        """
        Test that destination_create sends the right payload and returns
        a LogsDestination object.
        """
        create_response = {
            "id": 2,
            "label": "new-dest",
            "type": "akamai_object_storage",
            "status": "active",
            "details": {
                "access_key_id": "KEYID999",
                "bucket_name": "new-bucket",
                "host": "new-bucket.us-east-1.linodeobjects.com",
                "path": "logs/audit",
            },
            "created": "2024-07-01T00:00:00",
            "updated": "2024-07-01T00:00:00",
            "created_by": "tester",
            "updated_by": "tester",
            "version": 1,
        }

        with self.mock_post(create_response) as m:
            result = self.client.monitor.destination_create(
                label="new-dest",
                type="akamai_object_storage",
                access_key_id="KEYID999",
                access_key_secret="SUPERSECRET",
                bucket_name="new-bucket",
                host="new-bucket.us-east-1.linodeobjects.com",
                path="logs/audit",
            )

        self.assertEqual(m.call_url, "/monitor/streams/destinations")
        self.assertEqual(m.call_data["label"], "new-dest")
        self.assertEqual(m.call_data["type"], "akamai_object_storage")
        self.assertEqual(m.call_data["details"]["access_key_id"], "KEYID999")
        self.assertEqual(
            m.call_data["details"]["access_key_secret"], "SUPERSECRET"
        )
        self.assertEqual(m.call_data["details"]["bucket_name"], "new-bucket")
        self.assertEqual(
            m.call_data["details"]["host"],
            "new-bucket.us-east-1.linodeobjects.com",
        )
        self.assertEqual(m.call_data["details"]["path"], "logs/audit")

        self.assertIsInstance(result, LogsDestination)
        self.assertEqual(result.id, 2)
        self.assertEqual(result.label, "new-dest")

    def test_update_destination(self):
        """
        Test that mutating a LogsDestination's mutable fields and calling save()
        sends a PUT to the correct endpoint with the updated values.
        """
        dest = self.client.load(LogsDestination, 1)

        updated_response = {
            "id": 1,
            "label": "renamed-destination",
            "type": "akamai_object_storage",
            "status": "active",
            "details": {
                "access_key_id": "1ABCD23EFG4HIJKLMNO5",
                "bucket_name": "primary-bucket",
                "host": "primary-bucket.us-east-1.linodeobjects.com",
                "path": "audit-logs",
            },
            "created": "2024-06-01T12:00:00",
            "updated": "2024-06-03T08:00:00",
            "created_by": "tester",
            "updated_by": "tester",
            "version": 2,
        }

        with self.mock_put(updated_response) as m:
            dest.label = "renamed-destination"
            dest.save()

        self.assertEqual(m.call_url, "/monitor/streams/destinations/1")
        self.assertEqual(m.call_data["label"], "renamed-destination")

    def test_delete_destination(self):
        """
        Test that deleting a LogsDestination issues a DELETE to the correct URL.
        """
        dest = self.client.load(LogsDestination, 1)

        with self.mock_delete() as m:
            dest.delete()

        self.assertEqual(
            m.call_url, "/monitor/streams/destinations/1"
        )

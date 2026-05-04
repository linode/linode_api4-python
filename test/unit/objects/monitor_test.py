import datetime
from test.unit.base import ClientBaseCase

from linode_api4.objects import (
    AlertChannel,
    LogsDestination,
    LogsDestinationHistory,
    LogsStream,
    LogsStreamDestination,
    MonitorDashboard,
    MonitorService,
)
from linode_api4.objects.monitor import (
    AkamaiObjectStorageLogsDestinationDetails,
    CustomHTTPSLogsDestinationDetails,
    DestinationAuthentication,
    LogsDestinationDetailsBase,
    LogsStreamDetails,
    LogsStreamType,
)


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
        self.assertEqual(dest.created, datetime.datetime(2024, 6, 1, 12, 0, 0))
        self.assertEqual(dest.updated, datetime.datetime(2024, 6, 1, 12, 0, 0))
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
        self.assertIsInstance(snapshot, LogsDestinationHistory)
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

    def test_create_destination_akamai_object_storage(self):
        """
        Test that destination_create with type=akamai_object_storage sends the right
        payload and returns a LogsDestination object.
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
                details=AkamaiObjectStorageLogsDestinationDetails(
                    access_key_id="KEYID999",
                    access_key_secret="SUPERSECRET",
                    bucket_name="new-bucket",
                    host="new-bucket.us-east-1.linodeobjects.com",
                    path="logs/audit",
                ),
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

        self.assertEqual(m.call_url, "/monitor/streams/destinations/1")


class CustomHTTPSLogsDestinationTest(ClientBaseCase):
    """
    Tests for custom_https type LogsDestination and the load_by_type factory.
    """

    def test_load_by_type_factory(self):
        """load_by_type dispatches to the correct details class based on type."""
        akamai = LogsDestinationDetailsBase.load_by_type(
            "akamai_object_storage",
            {"access_key_id": "K", "bucket_name": "b", "host": "h.com"},
        )
        self.assertIsInstance(akamai, AkamaiObjectStorageLogsDestinationDetails)
        self.assertEqual(akamai.access_key_id, "K")

        custom = LogsDestinationDetailsBase.load_by_type(
            "custom_https",
            {
                "endpoint_url": "https://x.com",
                "authentication": {"type": "none"},
                "data_compression": "gzip",
                "content_type": "application/json",
            },
        )
        self.assertIsInstance(custom, CustomHTTPSLogsDestinationDetails)
        self.assertEqual(custom.endpoint_url, "https://x.com")

        self.assertIsNone(
            LogsDestinationDetailsBase.load_by_type("custom_https", None)
        )
        self.assertIsNone(
            LogsDestinationDetailsBase.load_by_type("custom_https", {})
        )
        self.assertIsNone(
            LogsDestinationDetailsBase.load_by_type("unknown", {"x": 1})
        )

    def test_load_custom_https_destination(self):
        """
        Loading a custom_https destination deserializes all nested fields correctly.
        """
        dest = self.client.load(LogsDestination, 2)

        self.assertIsInstance(dest.details, CustomHTTPSLogsDestinationDetails)
        self.assertEqual(
            dest.details.endpoint_url,
            "https://my-site.com/log-storage/basicAuth",
        )
        self.assertEqual(dest.details.data_compression, "gzip")
        self.assertEqual(dest.details.content_type, "application/json")
        self.assertEqual(dest.details.authentication.type, "basic")
        self.assertEqual(
            dest.details.authentication.details.basic_authentication_user,
            "John_Q",
        )
        self.assertEqual(dest.details.custom_headers[0].name, "Cache-Control")
        self.assertEqual(
            dest.details.client_certificate_details.tls_hostname, "my-site.com"
        )

    def test_stream_with_custom_https_destination(self):
        """
        A LogsStreamDestination with type custom_https is deserialized correctly.
        """
        stream = self.client.load(LogsStream, 2)
        details = stream.destinations[0].details

        self.assertIsInstance(details, CustomHTTPSLogsDestinationDetails)
        self.assertEqual(
            details.endpoint_url, "https://my-site.com/log-storage/basicAuth"
        )
        self.assertEqual(details.authentication.type, "basic")
        self.assertEqual(details.custom_headers[0].name, "Cache-Control")

    def test_create_custom_https_destination(self):
        """
        destination_create with type=custom_https sends the correct payload.
        """
        create_response = {
            "id": 3,
            "label": "new-custom-dest",
            "type": "custom_https",
            "status": "active",
            "details": {
                "endpoint_url": "https://example.com/logs",
                "authentication": {"type": "none"},
                "data_compression": "none",
                "content_type": "application/json",
            },
            "created": "2024-09-01T00:00:00",
            "updated": "2024-09-01T00:00:00",
            "created_by": "tester",
            "updated_by": "tester",
            "version": 1,
        }

        with self.mock_post(create_response) as m:
            result = self.client.monitor.destination_create(
                label="new-custom-dest",
                type="custom_https",
                details=CustomHTTPSLogsDestinationDetails(
                    endpoint_url="https://example.com/logs",
                    authentication=DestinationAuthentication(type="none"),
                    data_compression="none",
                    content_type="application/json",
                ),
            )

        self.assertEqual(m.call_url, "/monitor/streams/destinations")
        self.assertEqual(m.call_data["type"], "custom_https")
        self.assertEqual(
            m.call_data["details"]["endpoint_url"], "https://example.com/logs"
        )
        self.assertIsInstance(result, LogsDestination)
        self.assertEqual(result.id, 3)
        self.assertIsInstance(result.details, CustomHTTPSLogsDestinationDetails)


class LogsStreamTest(ClientBaseCase):
    """
    Tests methods for LogsStream class.
    """

    def test_list_streams(self):
        """
        Test that listing streams returns LogsStream objects with all fields populated.
        """
        streams = self.client.monitor.streams()

        self.assertEqual(len(streams), 1)
        stream = streams[0]
        self.assertIsInstance(stream, LogsStream)
        self.assertEqual(stream.id, 1)
        self.assertEqual(stream.label, "my-logs-stream")
        self.assertEqual(stream.type, "audit_logs")
        self.assertEqual(stream.status, "active")
        self.assertEqual(stream.version, 1)
        self.assertEqual(
            stream.created, datetime.datetime(2024, 6, 1, 12, 0, 0)
        )
        self.assertEqual(
            stream.updated, datetime.datetime(2024, 6, 1, 12, 0, 0)
        )
        self.assertEqual(stream.created_by, "tester")
        self.assertEqual(stream.updated_by, "tester")

    def test_list_streams_destinations(self):
        """
        Test that the nested destinations are deserialized as LogsStreamDestination objects.
        """
        stream = self.client.load(LogsStream, 1)

        self.assertIsNotNone(stream.destinations)
        self.assertEqual(len(stream.destinations), 1)
        dest = stream.destinations[0]
        self.assertIsInstance(dest, LogsStreamDestination)
        self.assertEqual(dest.id, 1)
        self.assertEqual(dest.label, "my-logs-destination")
        self.assertEqual(dest.type, "akamai_object_storage")
        self.assertIsNotNone(dest.details)
        self.assertEqual(dest.details.bucket_name, "primary-bucket")
        self.assertEqual(dest.details.access_key_id, "1ABCD23EFG4HIJKLMNO5")
        self.assertEqual(
            dest.details.host, "primary-bucket.us-east-1.linodeobjects.com"
        )
        self.assertEqual(dest.details.path, "audit-logs")

    def test_stream_history(self):
        """
        Test that the history property returns LogsStreamHistory objects.
        """
        stream = self.client.load(LogsStream, 1)
        history = stream.history

        self.assertEqual(len(history), 1)
        snapshot = history[0]
        self.assertEqual(snapshot.id, 1)
        self.assertEqual(snapshot.label, "my-logs-stream")
        self.assertEqual(snapshot.type, "audit_logs")
        self.assertEqual(snapshot.status, "active")
        self.assertEqual(snapshot.version, 2)
        self.assertEqual(
            snapshot.updated, datetime.datetime(2024, 6, 2, 9, 0, 0)
        )
        self.assertIsNotNone(snapshot.destinations)

    def test_create_stream(self):
        """
        Test that stream_create sends the correct payload and returns a LogsStream object.
        """
        create_response = {
            "id": 2,
            "label": "new-stream",
            "type": "audit_logs",
            "status": "active",
            "destinations": [
                {
                    "id": 1,
                    "label": "my-logs-destination",
                    "type": "akamai_object_storage",
                    "details": {},
                }
            ],
            "created": "2024-07-01T00:00:00",
            "updated": "2024-07-01T00:00:00",
            "created_by": "tester",
            "updated_by": "tester",
            "version": 1,
        }

        with self.mock_post(create_response) as m:
            result = self.client.monitor.stream_create(
                destinations=[1],
                label="new-stream",
                status="active",
                type="audit_logs",
            )

        self.assertEqual(m.call_url, "/monitor/streams")
        self.assertEqual(m.call_data["label"], "new-stream")
        self.assertEqual(m.call_data["type"], "audit_logs")
        self.assertEqual(m.call_data["status"], "active")
        self.assertEqual(m.call_data["destinations"], [1])

        self.assertIsInstance(result, LogsStream)
        self.assertEqual(result.id, 2)
        self.assertEqual(result.label, "new-stream")

    def test_update_stream_save(self):
        """
        Test that mutating a LogsStream's mutable fields and calling save()
        sends a PUT with correct payload.
        """
        stream = self.client.load(LogsStream, 1)

        updated_response = {
            "id": 1,
            "label": "renamed-stream",
            "type": "audit_logs",
            "status": "inactive",
            "destinations": [
                {
                    "id": 1,
                    "label": "my-logs-destination",
                    "type": "akamai_object_storage",
                    "details": {},
                }
            ],
            "created": "2024-06-01T12:00:00",
            "updated": "2024-06-03T08:00:00",
            "created_by": "tester",
            "updated_by": "tester",
            "version": 2,
        }

        with self.mock_put(updated_response) as m:
            stream.label = "renamed-stream"
            stream.status = "inactive"
            stream.save()

        self.assertEqual(m.call_url, "/monitor/streams/1")
        self.assertEqual(m.call_data["label"], "renamed-stream")
        self.assertEqual(m.call_data["status"], "inactive")

    def test_update_stream_destinations(self):
        """
        Test that update_destinations sends PUT request with flat destination ids list.
        """
        stream = self.client.load(LogsStream, 1)

        with self.mock_put({}) as m:
            result = stream.update_destinations([1])

        self.assertEqual(m.call_url, "/monitor/streams/1")
        self.assertEqual(m.call_data["destinations"], [1])
        self.assertTrue(result)

    def test_fail_update_stream_destinations_when_no_destination_ids_passed(
        self,
    ):
        """
        Test that update_destinations raises exception and doesn't send PUT request when id list is empty.
        """
        stream = self.client.load(LogsStream, 1)
        with self.mock_put({}) as m:
            with self.assertRaises(ValueError) as context:
                stream.update_destinations([])

        self.assertFalse(m.called)
        self.assertIn(
            "A destination id must be provided.", str(context.exception)
        )

    def test_delete_stream(self):
        """
        Test that deleting a LogsStream issues a DELETE to the correct URL.
        """
        stream = self.client.load(LogsStream, 1)

        with self.mock_delete() as m:
            stream.delete()

        self.assertEqual(m.call_url, "/monitor/streams/1")


class LkeAuditLogsStreamTest(ClientBaseCase):
    """
    Tests for lke_audit_logs stream type and LogsStreamDetails model.
    """

    def test_logs_stream_type_enum(self):
        """LogsStreamType exposes both audit_logs and lke_audit_logs values."""
        self.assertEqual(LogsStreamType.audit_logs, "audit_logs")
        self.assertEqual(LogsStreamType.lke_audit_logs, "lke_audit_logs")

    def test_load_lke_audit_logs_stream(self):
        """
        Loading an lke_audit_logs stream deserializes type and details correctly.
        """
        stream = self.client.load(LogsStream, 3)

        self.assertEqual(stream.id, 3)
        self.assertEqual(stream.type, "lke_audit_logs")
        self.assertIsInstance(stream.details, LogsStreamDetails)
        self.assertEqual(stream.details.cluster_ids, [1234, 5678])
        self.assertFalse(stream.details.is_auto_add_all_clusters_enabled)

    def test_audit_logs_stream_details_is_none(self):
        """An audit_logs stream has no details block."""
        stream = self.client.load(LogsStream, 1)
        self.assertIsNone(stream.details)

    def test_create_lke_audit_logs_stream(self):
        """
        stream_create with lke_audit_logs sends details in the payload.
        """
        create_response = {
            "id": 4,
            "label": "new-lke-stream",
            "type": "lke_audit_logs",
            "status": "active",
            "destinations": [
                {
                    "id": 1,
                    "label": "d",
                    "type": "akamai_object_storage",
                    "details": {},
                }
            ],
            "details": {
                "cluster_ids": [1111, 2222],
                "is_auto_add_all_clusters_enabled": False,
            },
            "created": "2024-10-01T12:00:00",
            "updated": "2024-10-01T12:00:00",
            "created_by": "tester",
            "updated_by": "tester",
            "version": 1,
        }

        with self.mock_post(create_response) as m:
            result = self.client.monitor.stream_create(
                destinations=[1],
                label="new-lke-stream",
                type=LogsStreamType.lke_audit_logs,
                details=LogsStreamDetails(
                    cluster_ids=[1111, 2222],
                    is_auto_add_all_clusters_enabled=False,
                ),
            )

        self.assertEqual(m.call_data["type"], "lke_audit_logs")
        self.assertEqual(m.call_data["details"]["cluster_ids"], [1111, 2222])
        self.assertFalse(
            m.call_data["details"]["is_auto_add_all_clusters_enabled"]
        )
        self.assertIsInstance(result.details, LogsStreamDetails)

    def test_create_audit_logs_stream_omits_details(self):
        """
        stream_create without details does not include a details key in the payload.
        """
        create_response = {
            "id": 5,
            "label": "new-audit-stream",
            "type": "audit_logs",
            "status": "active",
            "destinations": [
                {
                    "id": 1,
                    "label": "d",
                    "type": "akamai_object_storage",
                    "details": {},
                }
            ],
            "created": "2024-10-01T12:00:00",
            "updated": "2024-10-01T12:00:00",
            "created_by": "tester",
            "updated_by": "tester",
            "version": 1,
        }

        with self.mock_post(create_response) as m:
            self.client.monitor.stream_create(
                destinations=[1],
                label="new-audit-stream",
                type=LogsStreamType.audit_logs,
            )

        self.assertNotIn("details", m.call_data)

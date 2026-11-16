import json
from datetime import datetime, timedelta
from test.unit.base import ClientBaseCase, load_json

from mock import patch

from linode_api4 import (
    ApiError,
    DatabasePrivateNetwork,
    ExplicitNullValue,
    ValkeyDatabase,
    ValkeyDatabaseConfigOptions,
)


class ValkeyDatabaseTest(ClientBaseCase):
    def test_load_and_lazy_load(self):
        with self.mock_get("/databases/valkey/instances/123") as mock:
            db = ValkeyDatabase(self.client, 123)
            self.assertFalse(mock.called)
            self.assertEqual(db.id, 123)
            self.assertEqual(db.label, "example-valkey")
            self.assertEqual(mock.call_count, 1)
            self.assertEqual(mock.call_url, "/databases/valkey/instances/123")
            self.assertEqual(db.created, datetime(2026, 1, 1))
            self.assertEqual(db.updated, datetime(2026, 1, 1, 0, 10))
            self.assertEqual(db.hosts.endpoints[0].role, "primary")
            self.assertEqual(db.members.dict, {"192.0.2.1": "primary"})
            self.assertIsNone(db.used_disk_size_gb)
            self.assertEqual(db.total_disk_size_gb, 15)
            self.assertEqual(db.port, 6379)
            self.assertIsInstance(db.engine_config, ValkeyDatabaseConfigOptions)
            self.assertEqual(
                db.engine_config.dict,
                load_json("/databases/valkey/instances/123")["engine_config"],
            )
        self.assertEqual(self.client.load(ValkeyDatabase, 123).id, 123)

    def test_update(self):
        db = self.client.load(ValkeyDatabase, 123)
        db.label = "updated-valkey"
        db.allow_list = []
        db.cluster_size = 3
        db.region = "us-east"
        db.type = "g7-dedicated-8-4"
        db.version = "8.1"
        db.updates.day_of_week = 2
        db.engine_config = ValkeyDatabaseConfigOptions(
            valkey_timeout=0,
            frequent_snapshots=False,
            backup_hour=ExplicitNullValue(),
            backup_minute=ExplicitNullValue(),
            valkey_maxmemory_policy=ExplicitNullValue(),
        )
        db.private_network = DatabasePrivateNetwork(
            vpc_id=1234, subnet_id=5678, public_access=False
        )
        with self.mock_put({}) as mock:
            self.assertTrue(db.save())
            self.assertEqual(mock.call_url, "/databases/valkey/instances/123")
            data = mock.call_data
            self.assertEqual(
                set(data),
                {
                    "label",
                    "allow_list",
                    "cluster_size",
                    "region",
                    "type",
                    "version",
                    "updates",
                    "engine_config",
                    "private_network",
                },
            )
            self.assertEqual(data["label"], "updated-valkey")
            self.assertEqual(data["allow_list"], [])
            self.assertEqual(data["cluster_size"], 3)
            self.assertEqual(data["updates"]["day_of_week"], 2)
            self.assertEqual(
                data["engine_config"],
                {
                    "backup_hour": None,
                    "backup_minute": None,
                    "valkey_maxmemory_policy": None,
                    "valkey_timeout": 0,
                    "frequent_snapshots": False,
                },
            )
            self.assertIs(data["private_network"]["public_access"], False)

    def test_update_configuration_round_trip(self):
        db = self.client.load(ValkeyDatabase, 123)
        expected = db.engine_config.dict
        with self.mock_put({}) as mock:
            db.save()
            self.assertEqual(mock.call_data["engine_config"], expected)
        db.engine_config = {"valkey_timeout": 0, "frequent_snapshots": False}
        with self.mock_put({}) as mock:
            db.save()
            self.assertEqual(mock.call_data["engine_config"], db.engine_config)

    def test_nullable_fields(self):
        response = {
            **load_json("/databases/valkey/instances/123"),
            "private_network": None,
            "engine_config": None,
        }
        with self.mock_get(response):
            db = self.client.load(ValkeyDatabase, 123)
        self.assertIsNone(db.private_network)
        self.assertIsNone(db.engine_config)
        db.private_network = ExplicitNullValue()
        with self.mock_put({}) as mock:
            db.save()
            self.assertIsNone(json.loads(mock.call_data_raw)["private_network"])
        config = ValkeyDatabaseConfigOptions.from_json(
            {
                "backup_hour": None,
                "backup_minute": None,
                "valkey_maxmemory_policy": None,
            }
        )
        self.assertEqual(config.dict, {})

    def test_read_only_properties(self):
        db = self.client.load(ValkeyDatabase, 123)
        for key in (
            "engine",
            "available_restore_times",
            "status",
            "members",
            "port",
            "fork",
            "created",
            "updated",
            "total_disk_size_gb",
        ):
            with self.subTest(key=key), self.assertRaises(AttributeError):
                setattr(db, key, None)

    def test_volatile_status_refresh(self):
        db = self.client.load(ValkeyDatabase, 123)
        db._last_updated = datetime.now() - timedelta(seconds=30)
        response = {
            **load_json("/databases/valkey/instances/123"),
            "status": "suspended",
        }
        with self.mock_get(response) as mock:
            self.assertEqual(db.status, "suspended")
            self.assertEqual(mock.call_count, 1)

    def test_action_errors_propagate(self):
        for action in ("credentials_reset", "patch", "suspend", "resume"):
            with self.subTest(action=action):
                db = ValkeyDatabase(self.client, 123)
                error = ApiError("Cluster is not available", status=400)
                with patch.object(self.client, "post", side_effect=error):
                    with self.assertRaises(ApiError) as raised:
                        getattr(db, action)()
                    self.assertIs(raised.exception, error)

    def test_credentials_and_ssl_are_cached(self):
        db = ValkeyDatabase(self.client, 123)
        for name, response in (
            (
                "credentials",
                {
                    "username": "example-admin",
                    "password": "example-test-password",
                },
            ),
            ("ssl", {"ca_certificate": "ZXhhbXBsZS10ZXN0LWNlcnRpZmljYXRl"}),
        ):
            with self.subTest(name=name), self.mock_get(response) as mock:
                value = getattr(db, name)
                self.assertEqual(value.dict, response)
                self.assertIs(value, getattr(db, name))
                self.assertEqual(mock.call_count, 1)
                self.assertEqual(
                    mock.call_url, f"/databases/valkey/instances/123/{name}"
                )

    def test_actions_invalidate_caches(self):
        for action, path, expected in (
            ("credentials_reset", "credentials/reset", {}),
            ("patch", "patch", {}),
            ("suspend", "suspend", None),
            ("resume", "resume", None),
        ):
            with self.subTest(action=action):
                db = self.client.load(ValkeyDatabase, 123)
                credentials, ssl = db.credentials, db.ssl
                with self.mock_post(
                    f"/databases/valkey/instances/123/{path}"
                ) as mock:
                    self.assertEqual(getattr(db, action)(), expected)
                    self.assertEqual(
                        mock.call_url, f"/databases/valkey/instances/123/{path}"
                    )
                self.assertFalse(db._populated)
                self.assertNotIn("_credentials", vars(db))
                self.assertNotIn("_ssl", vars(db))
                self.assertEqual(db.id, 123)
                self.assertIsNot(db.credentials, credentials)
                self.assertIsNot(db.ssl, ssl)

    def test_delete(self):
        db = self.client.load(ValkeyDatabase, 123)
        db.credentials
        db.ssl
        with self.mock_delete() as mock:
            self.assertTrue(db.delete())
            self.assertEqual(mock.call_url, "/databases/valkey/instances/123")
        self.assertFalse(db._populated)
        self.assertNotIn("_credentials", vars(db))
        self.assertNotIn("_ssl", vars(db))

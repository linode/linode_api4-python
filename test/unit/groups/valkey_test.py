import json
from dataclasses import fields
from datetime import datetime, timedelta, timezone
from test.unit.base import ClientBaseCase, load_json

from mock import patch

from linode_api4 import (
    ApiError,
    Database,
    DatabaseEngine,
    DatabasePrivateNetwork,
    DatabaseType,
    ExplicitNullValue,
    MySQLDatabase,
    PaginatedList,
    PostgreSQLDatabase,
    Region,
    UnexpectedResponseError,
    ValkeyDatabase,
    ValkeyDatabaseConfigOptions,
)


class ValkeyGroupTest(ClientBaseCase):
    def setUp(self):
        super().setUp()
        self.response = load_json("/databases/valkey/instances/123")

    def test_list_and_filter(self):
        with self.mock_get("/databases/valkey/instances") as mock:
            databases = self.client.database.valkey_instances(
                ValkeyDatabase.label == "example-valkey"
            )
            self.assertIsInstance(databases, PaginatedList)
            self.assertEqual(len(databases), 1)
            self.assertIsInstance(databases[0], ValkeyDatabase)
            self.assertEqual(databases[0].id, 123)
            self.assertEqual(mock.call_url, "/databases/valkey/instances")
            self.assertEqual(
                json.loads(mock.call_headers["X-Filter"]),
                {"label": "example-valkey"},
            )

    def test_pagination(self):
        page = {
            "data": [self.response],
            "page": 1,
            "pages": 2,
            "results": 2,
        }
        with self.mock_get(page):
            databases = self.client.database.valkey_instances()
        page["page"] = 2
        page["data"] = [{**self.response, "id": 124}]
        with self.mock_get(page) as mock:
            self.assertEqual(databases[1].id, 124)
            self.assertIn("/databases/valkey/instances?page=2", mock.call_url)

    def test_config_catalog(self):
        with self.mock_get("/databases/valkey/config") as mock:
            config = self.client.database.valkey_config_options()
            self.assertEqual(mock.call_url, "/databases/valkey/config")
        self.assertEqual(config, load_json("/databases/valkey/config"))
        self.assertEqual(
            set(config),
            {field.name for field in fields(ValkeyDatabaseConfigOptions)},
        )
        self.assertEqual(config["backup_hour"]["type"], ["integer", "null"])
        self.assertEqual(config["backup_minute"]["maximum"], 59)
        self.assertEqual(config["valkey_timeout"]["type"], "integer")
        self.assertEqual(
            config["valkey_acl_channels_default"]["enum"],
            ["allchannels", "resetchannels"],
        )
        self.assertIs(config["valkey_activedefrag"]["example"], False)
        self.assertIs(config["frequent_snapshots"]["default"], True)
        self.assertEqual(
            config["valkey_maxmemory_policy"]["default"], "noeviction"
        )
        self.assertNotIn("default", config["valkey_persistence"])

    def test_create(self):
        config = ValkeyDatabaseConfigOptions.from_json(
            self.response["engine_config"]
        )
        network = DatabasePrivateNetwork(
            vpc_id=1234, subnet_id=5678, public_access=False
        )
        with self.mock_post(self.response) as mock:
            db = self.client.database.valkey_create(
                "example-valkey",
                Region(self.client, "us-east"),
                DatabaseEngine(self.client, "valkey/8.1"),
                DatabaseType(self.client, "g7-dedicated-4-2"),
                engine_config=config,
                private_network=network,
                cluster_size=1,
                allow_list=[],
                ssl_connection=True,
            )
            self.assertEqual(mock.call_url, "/databases/valkey/instances")
            self.assertEqual(
                mock.call_data,
                {
                    "label": "example-valkey",
                    "region": "us-east",
                    "engine": "valkey/8.1",
                    "type": "g7-dedicated-4-2",
                    "engine_config": self.response["engine_config"],
                    "private_network": self.response["private_network"],
                    "cluster_size": 1,
                    "allow_list": [],
                    "ssl_connection": True,
                },
            )
        self.assertIsInstance(db, ValkeyDatabase)
        self.assertEqual(db.id, 123)
        self.assertEqual(db.engine_config, config)

    def test_create_optional_configuration(self):
        for config in (None, {}, ValkeyDatabaseConfigOptions()):
            with (
                self.subTest(config=config),
                self.mock_post(self.response) as mock,
            ):
                self.client.database.valkey_create(
                    "example-valkey",
                    "us-east",
                    "valkey/8.1",
                    "g7-dedicated-4-2",
                    engine_config=config,
                )
                if config is None:
                    self.assertNotIn("engine_config", mock.call_data)
                else:
                    self.assertEqual(mock.call_data["engine_config"], {})
                self.assertNotIn("private_network", mock.call_data)

    def test_create_null_zero_false_and_dictionary_options(self):
        expected = {
            "backup_hour": None,
            "backup_minute": None,
            "valkey_maxmemory_policy": None,
            "frequent_snapshots": False,
            "valkey_timeout": 0,
        }
        configs = [
            ValkeyDatabaseConfigOptions(
                backup_hour=ExplicitNullValue(),
                backup_minute=ExplicitNullValue(),
                valkey_maxmemory_policy=ExplicitNullValue(),
                frequent_snapshots=False,
                valkey_timeout=0,
            ),
            {
                **expected,
                "backup_hour": ExplicitNullValue(),
                "backup_minute": ExplicitNullValue(),
                "valkey_maxmemory_policy": ExplicitNullValue(),
            },
        ]
        for config in configs:
            with (
                self.subTest(config=config),
                self.mock_post(self.response) as mock,
            ):
                self.client.database.valkey_create(
                    "example-valkey",
                    "us-east",
                    "valkey/8.1",
                    "g7-dedicated-4-2",
                    engine_config=config,
                )
                self.assertEqual(mock.call_data["engine_config"], expected)

    def test_missing_create_or_fork_id(self):
        for operation, args in (
            (
                self.client.database.valkey_create,
                ("example-valkey", "us-east", "valkey/8.1", "g7-dedicated-4-2"),
            ),
            (self.client.database.valkey_fork, (123,)),
        ):
            with self.subTest(operation=operation), self.mock_post({}):
                with self.assertRaises(UnexpectedResponseError):
                    operation(*args)

    def test_api_errors_propagate(self):
        error = ApiError("Valkey access is not enabled", status=403)
        with patch.object(self.client, "get", side_effect=error):
            for operation in (
                self.client.database.valkey_instances,
                self.client.database.valkey_config_options,
            ):
                with self.subTest(operation=operation):
                    with self.assertRaises(ApiError) as raised:
                        operation()
                    self.assertIs(raised.exception, error)
        with patch.object(self.client, "post", side_effect=error):
            with self.assertRaises(ApiError):
                self.client.database.valkey_create(
                    "example-valkey",
                    "us-east",
                    "valkey/8.1",
                    "g7-dedicated-4-2",
                )
            with self.assertRaises(ApiError):
                self.client.database.valkey_fork(123)

    def test_fork_restore_times(self):
        for restore_time, expected in (
            (None, {"source": 123}),
            (
                "2026-01-01T01:00:00",
                {"source": 123, "restore_time": "2026-01-01T01:00:00"},
            ),
            (
                datetime(2026, 1, 1, 1),
                {"source": 123, "restore_time": "2026-01-01T01:00:00"},
            ),
            (
                datetime(2026, 1, 1, 3, tzinfo=timezone(timedelta(hours=2))),
                {"source": 123, "restore_time": "2026-01-01T01:00:00"},
            ),
        ):
            with (
                self.subTest(restore_time=restore_time),
                self.mock_post(self.response) as mock,
            ):
                db = self.client.database.valkey_fork(123, restore_time)
                self.assertEqual(mock.call_url, "/databases/valkey/instances")
                self.assertEqual(mock.call_data, {"fork": expected})
                self.assertIsInstance(db, ValkeyDatabase)

    def test_fork_overrides(self):
        with self.mock_post(self.response) as mock:
            self.client.database.valkey_fork(
                123,
                label="forked",
                ltype=DatabaseType(self.client, "g7-dedicated-4-2"),
                region=Region(self.client, "us-east"),
                engine_config=ValkeyDatabaseConfigOptions(valkey_timeout=0),
                private_network=DatabasePrivateNetwork(vpc_id=1234),
            )
            self.assertEqual(
                mock.call_data,
                {
                    "fork": {"source": 123},
                    "label": "forked",
                    "type": "g7-dedicated-4-2",
                    "region": "us-east",
                    "engine_config": {"valkey_timeout": 0},
                    "private_network": {"vpc_id": 1234},
                },
            )
        with self.mock_post(self.response) as mock:
            self.client.database.valkey_fork(123, type="g7-dedicated-4-2")
            self.assertEqual(mock.call_data["type"], "g7-dedicated-4-2")

    def test_invalid_fork_inputs_do_not_send_requests(self):
        with self.mock_post(self.response) as mock:
            for value in (0, False, [], {}):
                with self.subTest(value=value), self.assertRaises(TypeError):
                    self.client.database.valkey_fork(123, value)
            for options in (
                {"ltype": "one", "type": "two"},
                {"fork": {"source": 1}},
            ):
                with (
                    self.subTest(options=options),
                    self.assertRaises(ValueError),
                ):
                    self.client.database.valkey_fork(123, **options)
            self.assertFalse(mock.called)

    def test_discovery_and_generic_database_translation(self):
        engines = self.client.database.engines()
        self.assertEqual(engines[2].engine, "valkey")
        self.assertEqual(engines[2].id, "valkey/8.1")
        self.assertEqual(
            self.client.database.types()[0].engines.valkey[0].quantity, 1
        )
        databases = self.client.database.instances()
        self.assertIsNone(databases[0].available_restore_times)
        self.assertIsInstance(databases[1].instance, ValkeyDatabase)
        self.assertIs(databases[1].instance, databases[1].instance)
        self.assertEqual(databases[1].instance.id, 123)
        self.assertEqual(databases[1].instance.label, "example-valkey")
        for engine, model in (
            ("mysql", MySQLDatabase),
            ("postgresql", PostgreSQLDatabase),
        ):
            self.assertIsInstance(
                Database(self.client, 123, {"engine": engine}).instance, model
            )
        self.assertIsNone(
            Database(self.client, 123, {"engine": "unknown"}).instance
        )

    def test_restore_list_shapes_and_round_trip(self):
        for model in (Database, ValkeyDatabase):
            for times in (None, [], ["2026-01-01T01:00:00"]):
                with self.subTest(model=model, times=times):
                    db = model(
                        self.client, 123, {"available_restore_times": times}
                    )
                    self.assertEqual(db.available_restore_times, times)
            db = model(self.client, 123, {"engine": "valkey"})
            self.assertIsNone(db.available_restore_times)
        snapshot = self.client.load(
            ValkeyDatabase, 123
        ).available_restore_times[0]
        with self.mock_post(self.response) as mock:
            self.client.database.valkey_fork(123, snapshot)
            self.assertEqual(mock.call_data["fork"]["restore_time"], snapshot)

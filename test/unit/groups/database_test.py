import logging
from test.unit.base import ClientBaseCase

from linode_api4.objects import MySQLDatabase

logger = logging.getLogger(__name__)


class DatabaseTest(ClientBaseCase):
    """
    Tests methods of the DatabaseGroup class
    """

    def test_get_types(self):
        """
        Test that database types are properly handled
        """
        types = self.client.database.types()

        self.assertEqual(len(types), 1)
        self.assertEqual(types[0].type_class, "nanode")
        self.assertEqual(types[0].id, "g6-nanode-1")
        self.assertEqual(types[0].engines.mysql[0].price.monthly, 20)

    def test_get_engines(self):
        """
        Test that database engines are properly handled
        """
        engines = self.client.database.engines()

        self.assertEqual(len(engines), 2)

        self.assertEqual(engines[0].engine, "mysql")
        self.assertEqual(engines[0].id, "mysql/8.0.26")
        self.assertEqual(engines[0].version, "8.0.26")

        self.assertEqual(engines[1].engine, "postgresql")
        self.assertEqual(engines[1].id, "postgresql/10.14")
        self.assertEqual(engines[1].version, "10.14")

    def test_get_databases(self):
        """
        Test that databases are properly handled
        """
        dbs = self.client.database.instances()

        self.assertEqual(len(dbs), 1)
        self.assertEqual(dbs[0].allow_list[1], "192.0.1.0/24")
        self.assertEqual(dbs[0].cluster_size, 3)
        self.assertEqual(dbs[0].encrypted, False)
        self.assertEqual(dbs[0].engine, "mysql")
        self.assertEqual(
            dbs[0].hosts.primary,
            "lin-123-456-mysql-mysql-primary.servers.linodedb.net",
        )
        self.assertEqual(
            dbs[0].hosts.secondary,
            "lin-123-456-mysql-primary-private.servers.linodedb.net",
        )
        self.assertEqual(dbs[0].id, 123)
        self.assertEqual(dbs[0].region, "us-east")
        self.assertEqual(dbs[0].updates.duration, 3)
        self.assertEqual(dbs[0].version, "8.0.26")

    def test_database_instance(self):
        """
        Ensures that the .instance attribute properly translates database types
        """

        dbs = self.client.database.instances()
        db_translated = dbs[0].instance

        self.assertTrue(isinstance(db_translated, MySQLDatabase))
        self.assertEqual(db_translated.ssl_connection, True)


class MySQLDatabaseTest(ClientBaseCase):
    """
    Tests methods of the MySQLDatabase class
    """

    def test_get_instances(self):
        """
        Test that database types are properly handled
        """
        dbs = self.client.database.mysql_instances()

        self.assertEqual(len(dbs), 1)
        self.assertEqual(dbs[0].allow_list[1], "192.0.1.0/24")
        self.assertEqual(dbs[0].cluster_size, 3)
        self.assertEqual(dbs[0].encrypted, False)
        self.assertEqual(dbs[0].engine, "mysql")
        self.assertEqual(
            dbs[0].hosts.primary,
            "lin-123-456-mysql-mysql-primary.servers.linodedb.net",
        )
        self.assertEqual(
            dbs[0].hosts.secondary,
            "lin-123-456-mysql-primary-private.servers.linodedb.net",
        )
        self.assertEqual(dbs[0].id, 123)
        self.assertEqual(dbs[0].region, "us-east")
        self.assertEqual(dbs[0].updates.duration, 3)
        self.assertEqual(dbs[0].version, "8.0.26")

    def test_create(self):
        """
        Test that MySQL databases can be created
        """

        with self.mock_post("/databases/mysql/instances") as m:
            # We don't care about errors here; we just want to
            # validate the request.
            try:
                self.client.database.mysql_create(
                    "cool",
                    "us-southeast",
                    "mysql/8.0.26",
                    "g6-standard-1",
                    cluster_size=3,
                )
            except Exception as e:
                logger.warning(
                    "An error occurred while validating the request: %s", e
                )

            self.assertEqual(m.method, "post")
            self.assertEqual(m.call_url, "/databases/mysql/instances")
            self.assertEqual(m.call_data["label"], "cool")
            self.assertEqual(m.call_data["region"], "us-southeast")
            self.assertEqual(m.call_data["engine"], "mysql/8.0.26")
            self.assertEqual(m.call_data["type"], "g6-standard-1")
            self.assertEqual(m.call_data["cluster_size"], 3)


class PostgreSQLDatabaseTest(ClientBaseCase):
    """
    Tests methods of the PostgreSQLDatabase class
    """

    def test_get_instances(self):
        """
        Test that database types are properly handled
        """
        dbs = self.client.database.postgresql_instances()

        self.assertEqual(len(dbs), 1)
        self.assertEqual(dbs[0].allow_list[1], "192.0.1.0/24")
        self.assertEqual(dbs[0].cluster_size, 3)
        self.assertEqual(dbs[0].encrypted, False)
        self.assertEqual(dbs[0].engine, "postgresql")
        self.assertEqual(
            dbs[0].hosts.primary,
            "lin-0000-000-pgsql-primary.servers.linodedb.net",
        )
        self.assertEqual(
            dbs[0].hosts.secondary,
            "lin-0000-000-pgsql-primary-private.servers.linodedb.net",
        )
        self.assertEqual(dbs[0].id, 123)
        self.assertEqual(dbs[0].region, "us-east")
        self.assertEqual(dbs[0].updates.duration, 3)
        self.assertEqual(dbs[0].version, "13.2")

    def test_create(self):
        """
        Test that PostgreSQL databases can be created
        """

        with self.mock_post("/databases/postgresql/instances") as m:
            # We don't care about errors here; we just want to
            # validate the request.
            try:
                self.client.database.postgresql_create(
                    "cool",
                    "us-southeast",
                    "postgresql/13.2",
                    "g6-standard-1",
                    cluster_size=3,
                )
            except Exception as e:
                logger.warning(
                    "An error occurred while validating the request: %s", e
                )

            self.assertEqual(m.method, "post")
            self.assertEqual(m.call_url, "/databases/postgresql/instances")
            self.assertEqual(m.call_data["label"], "cool")
            self.assertEqual(m.call_data["region"], "us-southeast")
            self.assertEqual(m.call_data["engine"], "postgresql/13.2")
            self.assertEqual(m.call_data["type"], "g6-standard-1")
            self.assertEqual(m.call_data["cluster_size"], 3)

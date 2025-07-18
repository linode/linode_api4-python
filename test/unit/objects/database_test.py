import logging
from test.unit.base import ClientBaseCase

from linode_api4 import (
    MySQLDatabaseConfigMySQLOptions,
    MySQLDatabaseConfigOptions,
    PostgreSQLDatabase,
    PostgreSQLDatabaseConfigOptions,
    PostgreSQLDatabaseConfigPGOptions,
)
from linode_api4.objects import MySQLDatabase

logger = logging.getLogger(__name__)


class MySQLDatabaseTest(ClientBaseCase):
    """
    Tests methods of the MySQLDatabase class
    """

    def test_create(self):
        """
        Test that MySQL databases can be created
        """

        logger = logging.getLogger(__name__)

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
                    engine_config=MySQLDatabaseConfigOptions(
                        mysql=MySQLDatabaseConfigMySQLOptions(
                            connect_timeout=20
                        ),
                        binlog_retention_period=200,
                    ),
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
            self.assertEqual(
                m.call_data["engine_config"]["mysql"]["connect_timeout"], 20
            )
            self.assertEqual(
                m.call_data["engine_config"]["binlog_retention_period"], 200
            )

    def test_update(self):
        """
        Test that the MySQL database can be updated
        """

        with self.mock_put("/databases/mysql/instances/123") as m:
            new_allow_list = ["192.168.0.1/32"]

            db = MySQLDatabase(self.client, 123)

            db.updates.day_of_week = 2
            db.allow_list = new_allow_list
            db.label = "cool"
            db.engine_config = MySQLDatabaseConfigOptions(
                mysql=MySQLDatabaseConfigMySQLOptions(connect_timeout=20),
                binlog_retention_period=200,
            )

            db.save()

            self.assertEqual(m.method, "put")
            self.assertEqual(m.call_url, "/databases/mysql/instances/123")
            self.assertEqual(m.call_data["label"], "cool")
            self.assertEqual(m.call_data["updates"]["day_of_week"], 2)
            self.assertEqual(m.call_data["allow_list"], new_allow_list)
            self.assertEqual(
                m.call_data["engine_config"]["mysql"]["connect_timeout"], 20
            )
            self.assertEqual(
                m.call_data["engine_config"]["binlog_retention_period"], 200
            )

    def test_list_backups(self):
        """
        Test that MySQL backups list properly
        """

        db = MySQLDatabase(self.client, 123)
        backups = db.backups

        self.assertEqual(len(backups), 1)

        self.assertEqual(backups[0].id, 456)
        self.assertEqual(
            backups[0].label, "Scheduled - 02/04/22 11:11 UTC-XcCRmI"
        )
        self.assertEqual(backups[0].type, "auto")

    def test_create_backup(self):
        """
        Test that MySQL database backups can be updated
        """

        with self.mock_post("/databases/mysql/instances/123/backups") as m:
            db = MySQLDatabase(self.client, 123)

            # We don't care about errors here; we just want to
            # validate the request.
            try:
                db.backup_create("mybackup", target="secondary")
            except Exception as e:
                logger.warning(
                    "An error occurred while validating the request: %s", e
                )

            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_url, "/databases/mysql/instances/123/backups"
            )
            self.assertEqual(m.call_data["label"], "mybackup")
            self.assertEqual(m.call_data["target"], "secondary")

    def test_backup_restore(self):
        """
        Test that MySQL database backups can be restored
        """

        with self.mock_post(
            "/databases/mysql/instances/123/backups/456/restore"
        ) as m:
            db = MySQLDatabase(self.client, 123)

            db.backups[0].restore()

            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_url, "/databases/mysql/instances/123/backups/456/restore"
            )

    def test_patch(self):
        """
        Test MySQL Database patching logic.
        """
        with self.mock_post("/databases/mysql/instances/123/patch") as m:
            db = MySQLDatabase(self.client, 123)

            db.patch()

            self.assertEqual(m.method, "post")
            self.assertEqual(m.call_url, "/databases/mysql/instances/123/patch")

    def test_get_ssl(self):
        """
        Test MySQL SSL cert logic
        """
        db = MySQLDatabase(self.client, 123)

        ssl = db.ssl

        self.assertEqual(ssl.ca_certificate, "LS0tLS1CRUdJ...==")

    def test_get_credentials(self):
        """
        Test MySQL credentials logic
        """
        db = MySQLDatabase(self.client, 123)

        creds = db.credentials

        self.assertEqual(creds.password, "s3cur3P@ssw0rd")
        self.assertEqual(creds.username, "linroot")

    def test_reset_credentials(self):
        """
        Test resetting MySQL credentials
        """
        with self.mock_post(
            "/databases/mysql/instances/123/credentials/reset"
        ) as m:
            db = MySQLDatabase(self.client, 123)

            db.credentials_reset()

            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_url, "/databases/mysql/instances/123/credentials/reset"
            )

    def test_suspend(self):
        """
        Test MySQL Database suspend logic.
        """
        with self.mock_post("/databases/mysql/instances/123/suspend") as m:
            db = MySQLDatabase(self.client, 123)

            db.suspend()

            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_url, "/databases/mysql/instances/123/suspend"
            )

    def test_resume(self):
        """
        Test MySQL Database resume logic.
        """
        with self.mock_post("/databases/mysql/instances/123/resume") as m:
            db = MySQLDatabase(self.client, 123)

            db.resume()

            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_url, "/databases/mysql/instances/123/resume"
            )


class PostgreSQLDatabaseTest(ClientBaseCase):
    """
    Tests methods of the PostgreSQLDatabase class
    """

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
                    engine_config=PostgreSQLDatabaseConfigOptions(
                        pg=PostgreSQLDatabaseConfigPGOptions(
                            autovacuum_analyze_scale_factor=0.5,
                            pg_partman_bgw_interval=3600,
                            pg_partman_bgw_role="myrolename",
                            pg_stat_monitor_pgsm_enable_query_plan=False,
                            pg_stat_monitor_pgsm_max_buckets=10,
                            pg_stat_statements_track="top",
                        ),
                        work_mem=4,
                    ),
                )
            except Exception:
                pass

            self.assertEqual(m.method, "post")
            self.assertEqual(m.call_url, "/databases/postgresql/instances")
            self.assertEqual(m.call_data["label"], "cool")
            self.assertEqual(m.call_data["region"], "us-southeast")
            self.assertEqual(m.call_data["engine"], "postgresql/13.2")
            self.assertEqual(m.call_data["type"], "g6-standard-1")
            self.assertEqual(m.call_data["cluster_size"], 3)
            self.assertEqual(
                m.call_data["engine_config"]["pg"][
                    "autovacuum_analyze_scale_factor"
                ],
                0.5,
            )
            self.assertEqual(
                m.call_data["engine_config"]["pg"]["pg_partman_bgw.interval"],
                3600,
            )
            self.assertEqual(
                m.call_data["engine_config"]["pg"]["pg_partman_bgw.role"],
                "myrolename",
            )
            self.assertEqual(
                m.call_data["engine_config"]["pg"][
                    "pg_stat_monitor.pgsm_enable_query_plan"
                ],
                False,
            )
            self.assertEqual(
                m.call_data["engine_config"]["pg"][
                    "pg_stat_monitor.pgsm_max_buckets"
                ],
                10,
            )
            self.assertEqual(
                m.call_data["engine_config"]["pg"]["pg_stat_statements.track"],
                "top",
            )
            self.assertEqual(m.call_data["engine_config"]["work_mem"], 4)

    def test_update(self):
        """
        Test that the PostgreSQL database can be updated
        """

        with self.mock_put("/databases/postgresql/instances/123") as m:
            new_allow_list = ["192.168.0.1/32"]

            db = PostgreSQLDatabase(self.client, 123)

            db.updates.day_of_week = 2
            db.allow_list = new_allow_list
            db.label = "cool"
            db.engine_config = PostgreSQLDatabaseConfigOptions(
                pg=PostgreSQLDatabaseConfigPGOptions(
                    autovacuum_analyze_scale_factor=0.5
                ),
                work_mem=4,
            )

            db.save()

            self.assertEqual(m.method, "put")
            self.assertEqual(m.call_url, "/databases/postgresql/instances/123")
            self.assertEqual(m.call_data["label"], "cool")
            self.assertEqual(m.call_data["updates"]["day_of_week"], 2)
            self.assertEqual(m.call_data["allow_list"], new_allow_list)
            self.assertEqual(
                m.call_data["engine_config"]["pg"][
                    "autovacuum_analyze_scale_factor"
                ],
                0.5,
            )
            self.assertEqual(m.call_data["engine_config"]["work_mem"], 4)

    def test_list_backups(self):
        """
        Test that PostgreSQL backups list properly
        """

        db = PostgreSQLDatabase(self.client, 123)
        backups = db.backups

        self.assertEqual(len(backups), 1)

        self.assertEqual(backups[0].id, 456)
        self.assertEqual(
            backups[0].label, "Scheduled - 02/04/22 11:11 UTC-XcCRmI"
        )
        self.assertEqual(backups[0].type, "auto")

    def test_create_backup(self):
        """
        Test that PostgreSQL database backups can be created
        """

        with self.mock_post("/databases/postgresql/instances/123/backups") as m:
            db = PostgreSQLDatabase(self.client, 123)

            # We don't care about errors here; we just want to
            # validate the request.
            try:
                db.backup_create("mybackup", target="secondary")
            except Exception as e:
                logger.warning(
                    "An error occurred while validating the request: %s", e
                )

            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_url, "/databases/postgresql/instances/123/backups"
            )
            self.assertEqual(m.call_data["label"], "mybackup")
            self.assertEqual(m.call_data["target"], "secondary")

    def test_backup_restore(self):
        """
        Test that PostgreSQL database backups can be restored
        """

        with self.mock_post(
            "/databases/postgresql/instances/123/backups/456/restore"
        ) as m:
            db = PostgreSQLDatabase(self.client, 123)

            db.backups[0].restore()

            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_url,
                "/databases/postgresql/instances/123/backups/456/restore",
            )

    def test_patch(self):
        """
        Test PostgreSQL Database patching logic.
        """
        with self.mock_post("/databases/postgresql/instances/123/patch") as m:
            db = PostgreSQLDatabase(self.client, 123)

            db.patch()

            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_url, "/databases/postgresql/instances/123/patch"
            )

    def test_get_ssl(self):
        """
        Test PostgreSQL SSL cert logic
        """
        db = PostgreSQLDatabase(self.client, 123)

        ssl = db.ssl

        self.assertEqual(ssl.ca_certificate, "LS0tLS1CRUdJ...==")

    def test_get_credentials(self):
        """
        Test PostgreSQL credentials logic
        """
        db = PostgreSQLDatabase(self.client, 123)

        creds = db.credentials

        self.assertEqual(creds.password, "s3cur3P@ssw0rd")
        self.assertEqual(creds.username, "linroot")

    def test_reset_credentials(self):
        """
        Test resetting PostgreSQL credentials
        """
        with self.mock_post(
            "/databases/postgresql/instances/123/credentials/reset"
        ) as m:
            db = PostgreSQLDatabase(self.client, 123)

            db.credentials_reset()

            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_url,
                "/databases/postgresql/instances/123/credentials/reset",
            )

    def test_suspend(self):
        """
        Test PostgreSQL Database suspend logic.
        """
        with self.mock_post("/databases/postgresql/instances/123/suspend") as m:
            db = PostgreSQLDatabase(self.client, 123)

            db.suspend()

            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_url, "/databases/postgresql/instances/123/suspend"
            )

    def test_resume(self):
        """
        Test PostgreSQL Database resume logic.
        """
        with self.mock_post("/databases/postgresql/instances/123/resume") as m:
            db = PostgreSQLDatabase(self.client, 123)

            db.resume()

            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_url, "/databases/postgresql/instances/123/resume"
            )

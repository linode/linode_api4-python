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
        self.assertEqual(dbs[0].engine_config.binlog_retention_period, 600)
        self.assertEqual(dbs[0].engine_config.mysql.connect_timeout, 10)
        self.assertEqual(dbs[0].engine_config.mysql.default_time_zone, "+03:00")
        self.assertEqual(dbs[0].engine_config.mysql.group_concat_max_len, 1024)
        self.assertEqual(
            dbs[0].engine_config.mysql.information_schema_stats_expiry, 86400
        )
        self.assertEqual(
            dbs[0].engine_config.mysql.innodb_change_buffer_max_size, 30
        )
        self.assertEqual(dbs[0].engine_config.mysql.innodb_flush_neighbors, 0)
        self.assertEqual(dbs[0].engine_config.mysql.innodb_ft_min_token_size, 3)
        self.assertEqual(
            dbs[0].engine_config.mysql.innodb_ft_server_stopword_table,
            "db_name/table_name",
        )
        self.assertEqual(
            dbs[0].engine_config.mysql.innodb_lock_wait_timeout, 50
        )
        self.assertEqual(
            dbs[0].engine_config.mysql.innodb_log_buffer_size, 16777216
        )
        self.assertEqual(
            dbs[0].engine_config.mysql.innodb_online_alter_log_max_size,
            134217728,
        )
        self.assertEqual(dbs[0].engine_config.mysql.innodb_read_io_threads, 10)
        self.assertTrue(dbs[0].engine_config.mysql.innodb_rollback_on_timeout)
        self.assertEqual(
            dbs[0].engine_config.mysql.innodb_thread_concurrency, 10
        )
        self.assertEqual(dbs[0].engine_config.mysql.innodb_write_io_threads, 10)
        self.assertEqual(dbs[0].engine_config.mysql.interactive_timeout, 3600)
        self.assertEqual(
            dbs[0].engine_config.mysql.internal_tmp_mem_storage_engine,
            "TempTable",
        )
        self.assertEqual(
            dbs[0].engine_config.mysql.max_allowed_packet, 67108864
        )
        self.assertEqual(
            dbs[0].engine_config.mysql.max_heap_table_size, 16777216
        )
        self.assertEqual(dbs[0].engine_config.mysql.net_buffer_length, 16384)
        self.assertEqual(dbs[0].engine_config.mysql.net_read_timeout, 30)
        self.assertEqual(dbs[0].engine_config.mysql.net_write_timeout, 30)
        self.assertEqual(dbs[0].engine_config.mysql.sort_buffer_size, 262144)
        self.assertEqual(
            dbs[0].engine_config.mysql.sql_mode, "ANSI,TRADITIONAL"
        )
        self.assertTrue(dbs[0].engine_config.mysql.sql_require_primary_key)
        self.assertEqual(dbs[0].engine_config.mysql.tmp_table_size, 16777216)
        self.assertEqual(dbs[0].engine_config.mysql.wait_timeout, 28800)

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

        print(dbs[0].engine_config.pg.__dict__)

        self.assertTrue(dbs[0].engine_config.pg_stat_monitor_enable)
        self.assertEqual(
            dbs[0].engine_config.pglookout.max_failover_replication_time_lag,
            1000,
        )
        self.assertEqual(dbs[0].engine_config.shared_buffers_percentage, 41.5)
        self.assertEqual(dbs[0].engine_config.work_mem, 4)
        self.assertEqual(
            dbs[0].engine_config.pg.autovacuum_analyze_scale_factor, 0.5
        )
        self.assertEqual(
            dbs[0].engine_config.pg.autovacuum_analyze_threshold, 100
        )
        self.assertEqual(dbs[0].engine_config.pg.autovacuum_max_workers, 10)
        self.assertEqual(dbs[0].engine_config.pg.autovacuum_naptime, 100)
        self.assertEqual(
            dbs[0].engine_config.pg.autovacuum_vacuum_cost_delay, 50
        )
        self.assertEqual(
            dbs[0].engine_config.pg.autovacuum_vacuum_cost_limit, 100
        )
        self.assertEqual(
            dbs[0].engine_config.pg.autovacuum_vacuum_scale_factor, 0.5
        )
        self.assertEqual(
            dbs[0].engine_config.pg.autovacuum_vacuum_threshold, 100
        )
        self.assertEqual(dbs[0].engine_config.pg.bgwriter_delay, 200)
        self.assertEqual(dbs[0].engine_config.pg.bgwriter_flush_after, 512)
        self.assertEqual(dbs[0].engine_config.pg.bgwriter_lru_maxpages, 100)
        self.assertEqual(dbs[0].engine_config.pg.bgwriter_lru_multiplier, 2.0)
        self.assertEqual(dbs[0].engine_config.pg.deadlock_timeout, 1000)
        self.assertEqual(
            dbs[0].engine_config.pg.default_toast_compression, "lz4"
        )
        self.assertEqual(
            dbs[0].engine_config.pg.idle_in_transaction_session_timeout, 100
        )
        self.assertTrue(dbs[0].engine_config.pg.jit)
        self.assertEqual(dbs[0].engine_config.pg.max_files_per_process, 100)
        self.assertEqual(dbs[0].engine_config.pg.max_locks_per_transaction, 100)
        self.assertEqual(
            dbs[0].engine_config.pg.max_logical_replication_workers, 32
        )
        self.assertEqual(dbs[0].engine_config.pg.max_parallel_workers, 64)
        self.assertEqual(
            dbs[0].engine_config.pg.max_parallel_workers_per_gather, 64
        )
        self.assertEqual(
            dbs[0].engine_config.pg.max_pred_locks_per_transaction, 1000
        )
        self.assertEqual(dbs[0].engine_config.pg.max_replication_slots, 32)
        self.assertEqual(dbs[0].engine_config.pg.max_slot_wal_keep_size, 100)
        self.assertEqual(dbs[0].engine_config.pg.max_stack_depth, 3507152)
        self.assertEqual(
            dbs[0].engine_config.pg.max_standby_archive_delay, 1000
        )
        self.assertEqual(
            dbs[0].engine_config.pg.max_standby_streaming_delay, 1000
        )
        self.assertEqual(dbs[0].engine_config.pg.max_wal_senders, 32)
        self.assertEqual(dbs[0].engine_config.pg.max_worker_processes, 64)
        self.assertEqual(
            dbs[0].engine_config.pg.password_encryption, "scram-sha-256"
        )
        self.assertEqual(dbs[0].engine_config.pg.pg_partman_bgw_interval, 3600)
        self.assertEqual(
            dbs[0].engine_config.pg.pg_partman_bgw_role, "myrolename"
        )
        self.assertFalse(
            dbs[0].engine_config.pg.pg_stat_monitor_pgsm_enable_query_plan
        )
        self.assertEqual(
            dbs[0].engine_config.pg.pg_stat_monitor_pgsm_max_buckets, 10
        )
        self.assertEqual(
            dbs[0].engine_config.pg.pg_stat_statements_track, "top"
        )
        self.assertEqual(dbs[0].engine_config.pg.temp_file_limit, 5000000)
        self.assertEqual(dbs[0].engine_config.pg.timezone, "Europe/Helsinki")
        self.assertEqual(
            dbs[0].engine_config.pg.track_activity_query_size, 1024
        )
        self.assertEqual(dbs[0].engine_config.pg.track_commit_timestamp, "off")
        self.assertEqual(dbs[0].engine_config.pg.track_functions, "all")
        self.assertEqual(dbs[0].engine_config.pg.track_io_timing, "off")
        self.assertEqual(dbs[0].engine_config.pg.wal_sender_timeout, 60000)
        self.assertEqual(dbs[0].engine_config.pg.wal_writer_delay, 50)

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

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

    def test_mysql_config_options(self):
        """
        Test that MySQL configuration options can be retrieved
        """

        config = self.client.database.mysql_config_options()

        self.assertEqual(
            "The number of seconds that the mysqld server waits for a connect packet before responding with Bad handshake",
            config["mysql"]["connect_timeout"]["description"],
        )
        self.assertEqual(10, config["mysql"]["connect_timeout"]["example"])
        self.assertEqual(3600, config["mysql"]["connect_timeout"]["maximum"])
        self.assertEqual(2, config["mysql"]["connect_timeout"]["minimum"])
        self.assertFalse(config["mysql"]["connect_timeout"]["requires_restart"])
        self.assertEqual("integer", config["mysql"]["connect_timeout"]["type"])

        self.assertEqual(
            "Default server time zone as an offset from UTC (from -12:00 to +12:00), a time zone name, or 'SYSTEM' to use the MySQL server default.",
            config["mysql"]["default_time_zone"]["description"],
        )
        self.assertEqual(
            "+03:00", config["mysql"]["default_time_zone"]["example"]
        )
        self.assertEqual(100, config["mysql"]["default_time_zone"]["maxLength"])
        self.assertEqual(2, config["mysql"]["default_time_zone"]["minLength"])
        self.assertEqual(
            "^([-+][\\d:]*|[\\w/]*)$",
            config["mysql"]["default_time_zone"]["pattern"],
        )
        self.assertFalse(
            config["mysql"]["default_time_zone"]["requires_restart"]
        )
        self.assertEqual("string", config["mysql"]["default_time_zone"]["type"])

        self.assertEqual(
            "The maximum permitted result length in bytes for the GROUP_CONCAT() function.",
            config["mysql"]["group_concat_max_len"]["description"],
        )
        self.assertEqual(
            1024, config["mysql"]["group_concat_max_len"]["example"]
        )
        self.assertEqual(
            18446744073709551600,
            config["mysql"]["group_concat_max_len"]["maximum"],
        )
        self.assertEqual(4, config["mysql"]["group_concat_max_len"]["minimum"])
        self.assertFalse(
            config["mysql"]["group_concat_max_len"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["mysql"]["group_concat_max_len"]["type"]
        )

        self.assertEqual(
            "The time, in seconds, before cached statistics expire",
            config["mysql"]["information_schema_stats_expiry"]["description"],
        )
        self.assertEqual(
            86400, config["mysql"]["information_schema_stats_expiry"]["example"]
        )
        self.assertEqual(
            31536000,
            config["mysql"]["information_schema_stats_expiry"]["maximum"],
        )
        self.assertEqual(
            900, config["mysql"]["information_schema_stats_expiry"]["minimum"]
        )
        self.assertFalse(
            config["mysql"]["information_schema_stats_expiry"][
                "requires_restart"
            ]
        )
        self.assertEqual(
            "integer",
            config["mysql"]["information_schema_stats_expiry"]["type"],
        )

        self.assertEqual(
            "Maximum size for the InnoDB change buffer, as a percentage of the total size of the buffer pool. Default is 25",
            config["mysql"]["innodb_change_buffer_max_size"]["description"],
        )
        self.assertEqual(
            30, config["mysql"]["innodb_change_buffer_max_size"]["example"]
        )
        self.assertEqual(
            50, config["mysql"]["innodb_change_buffer_max_size"]["maximum"]
        )
        self.assertEqual(
            0, config["mysql"]["innodb_change_buffer_max_size"]["minimum"]
        )
        self.assertFalse(
            config["mysql"]["innodb_change_buffer_max_size"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["mysql"]["innodb_change_buffer_max_size"]["type"]
        )

        self.assertEqual(
            "Specifies whether flushing a page from the InnoDB buffer pool also flushes other dirty pages in the same extent (default is 1): 0 - dirty pages in the same extent are not flushed, 1 - flush contiguous dirty pages in the same extent, 2 - flush dirty pages in the same extent",
            config["mysql"]["innodb_flush_neighbors"]["description"],
        )
        self.assertEqual(
            0, config["mysql"]["innodb_flush_neighbors"]["example"]
        )
        self.assertEqual(
            2, config["mysql"]["innodb_flush_neighbors"]["maximum"]
        )
        self.assertEqual(
            0, config["mysql"]["innodb_flush_neighbors"]["minimum"]
        )
        self.assertFalse(
            config["mysql"]["innodb_flush_neighbors"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["mysql"]["innodb_flush_neighbors"]["type"]
        )

        self.assertEqual(
            "Minimum length of words that are stored in an InnoDB FULLTEXT index. Changing this parameter will lead to a restart of the MySQL service.",
            config["mysql"]["innodb_ft_min_token_size"]["description"],
        )
        self.assertEqual(
            3, config["mysql"]["innodb_ft_min_token_size"]["example"]
        )
        self.assertEqual(
            16, config["mysql"]["innodb_ft_min_token_size"]["maximum"]
        )
        self.assertEqual(
            0, config["mysql"]["innodb_ft_min_token_size"]["minimum"]
        )
        self.assertTrue(
            config["mysql"]["innodb_ft_min_token_size"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["mysql"]["innodb_ft_min_token_size"]["type"]
        )

        self.assertEqual(
            "This option is used to specify your own InnoDB FULLTEXT index stopword list for all InnoDB tables.",
            config["mysql"]["innodb_ft_server_stopword_table"]["description"],
        )
        self.assertEqual(
            "db_name/table_name",
            config["mysql"]["innodb_ft_server_stopword_table"]["example"],
        )
        self.assertEqual(
            1024,
            config["mysql"]["innodb_ft_server_stopword_table"]["maxLength"],
        )
        self.assertEqual(
            "^.+/.+$",
            config["mysql"]["innodb_ft_server_stopword_table"]["pattern"],
        )
        self.assertFalse(
            config["mysql"]["innodb_ft_server_stopword_table"][
                "requires_restart"
            ]
        )
        self.assertEqual(
            ["null", "string"],
            config["mysql"]["innodb_ft_server_stopword_table"]["type"],
        )

        self.assertEqual(
            "The length of time in seconds an InnoDB transaction waits for a row lock before giving up. Default is 120.",
            config["mysql"]["innodb_lock_wait_timeout"]["description"],
        )
        self.assertEqual(
            50, config["mysql"]["innodb_lock_wait_timeout"]["example"]
        )
        self.assertEqual(
            3600, config["mysql"]["innodb_lock_wait_timeout"]["maximum"]
        )
        self.assertEqual(
            1, config["mysql"]["innodb_lock_wait_timeout"]["minimum"]
        )
        self.assertFalse(
            config["mysql"]["innodb_lock_wait_timeout"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["mysql"]["innodb_lock_wait_timeout"]["type"]
        )

        self.assertEqual(
            "The size in bytes of the buffer that InnoDB uses to write to the log files on disk.",
            config["mysql"]["innodb_log_buffer_size"]["description"],
        )
        self.assertEqual(
            16777216, config["mysql"]["innodb_log_buffer_size"]["example"]
        )
        self.assertEqual(
            4294967295, config["mysql"]["innodb_log_buffer_size"]["maximum"]
        )
        self.assertEqual(
            1048576, config["mysql"]["innodb_log_buffer_size"]["minimum"]
        )
        self.assertFalse(
            config["mysql"]["innodb_log_buffer_size"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["mysql"]["innodb_log_buffer_size"]["type"]
        )

        self.assertEqual(
            "The upper limit in bytes on the size of the temporary log files used during online DDL operations for InnoDB tables.",
            config["mysql"]["innodb_online_alter_log_max_size"]["description"],
        )
        self.assertEqual(
            134217728,
            config["mysql"]["innodb_online_alter_log_max_size"]["example"],
        )
        self.assertEqual(
            1099511627776,
            config["mysql"]["innodb_online_alter_log_max_size"]["maximum"],
        )
        self.assertEqual(
            65536,
            config["mysql"]["innodb_online_alter_log_max_size"]["minimum"],
        )
        self.assertFalse(
            config["mysql"]["innodb_online_alter_log_max_size"][
                "requires_restart"
            ]
        )
        self.assertEqual(
            "integer",
            config["mysql"]["innodb_online_alter_log_max_size"]["type"],
        )

        self.assertEqual(
            "The number of I/O threads for read operations in InnoDB. Default is 4. Changing this parameter will lead to a restart of the MySQL service.",
            config["mysql"]["innodb_read_io_threads"]["description"],
        )
        self.assertEqual(
            10, config["mysql"]["innodb_read_io_threads"]["example"]
        )
        self.assertEqual(
            64, config["mysql"]["innodb_read_io_threads"]["maximum"]
        )
        self.assertEqual(
            1, config["mysql"]["innodb_read_io_threads"]["minimum"]
        )
        self.assertTrue(
            config["mysql"]["innodb_read_io_threads"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["mysql"]["innodb_read_io_threads"]["type"]
        )

        self.assertEqual(
            "When enabled a transaction timeout causes InnoDB to abort and roll back the entire transaction. Changing this parameter will lead to a restart of the MySQL service.",
            config["mysql"]["innodb_rollback_on_timeout"]["description"],
        )
        self.assertTrue(
            config["mysql"]["innodb_rollback_on_timeout"]["example"]
        )
        self.assertTrue(
            config["mysql"]["innodb_rollback_on_timeout"]["requires_restart"]
        )
        self.assertEqual(
            "boolean", config["mysql"]["innodb_rollback_on_timeout"]["type"]
        )

        self.assertEqual(
            "Defines the maximum number of threads permitted inside of InnoDB. Default is 0 (infinite concurrency - no limit)",
            config["mysql"]["innodb_thread_concurrency"]["description"],
        )
        self.assertEqual(
            10, config["mysql"]["innodb_thread_concurrency"]["example"]
        )
        self.assertEqual(
            1000, config["mysql"]["innodb_thread_concurrency"]["maximum"]
        )
        self.assertEqual(
            0, config["mysql"]["innodb_thread_concurrency"]["minimum"]
        )
        self.assertFalse(
            config["mysql"]["innodb_thread_concurrency"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["mysql"]["innodb_thread_concurrency"]["type"]
        )

        self.assertEqual(
            "The number of I/O threads for write operations in InnoDB. Default is 4. Changing this parameter will lead to a restart of the MySQL service.",
            config["mysql"]["innodb_write_io_threads"]["description"],
        )
        self.assertEqual(
            10, config["mysql"]["innodb_write_io_threads"]["example"]
        )
        self.assertEqual(
            64, config["mysql"]["innodb_write_io_threads"]["maximum"]
        )
        self.assertEqual(
            1, config["mysql"]["innodb_write_io_threads"]["minimum"]
        )
        self.assertTrue(
            config["mysql"]["innodb_write_io_threads"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["mysql"]["innodb_write_io_threads"]["type"]
        )

        self.assertEqual(
            "The number of seconds the server waits for activity on an interactive connection before closing it.",
            config["mysql"]["interactive_timeout"]["description"],
        )
        self.assertEqual(
            3600, config["mysql"]["interactive_timeout"]["example"]
        )
        self.assertEqual(
            604800, config["mysql"]["interactive_timeout"]["maximum"]
        )
        self.assertEqual(30, config["mysql"]["interactive_timeout"]["minimum"])
        self.assertFalse(
            config["mysql"]["interactive_timeout"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["mysql"]["interactive_timeout"]["type"]
        )

        self.assertEqual(
            "The storage engine for in-memory internal temporary tables.",
            config["mysql"]["internal_tmp_mem_storage_engine"]["description"],
        )
        self.assertEqual(
            "TempTable",
            config["mysql"]["internal_tmp_mem_storage_engine"]["example"],
        )
        self.assertEqual(
            ["TempTable", "MEMORY"],
            config["mysql"]["internal_tmp_mem_storage_engine"]["enum"],
        )
        self.assertFalse(
            config["mysql"]["internal_tmp_mem_storage_engine"][
                "requires_restart"
            ]
        )
        self.assertEqual(
            "string", config["mysql"]["internal_tmp_mem_storage_engine"]["type"]
        )

        self.assertEqual(
            "Size of the largest message in bytes that can be received by the server. Default is 67108864 (64M)",
            config["mysql"]["max_allowed_packet"]["description"],
        )
        self.assertEqual(
            67108864, config["mysql"]["max_allowed_packet"]["example"]
        )
        self.assertEqual(
            1073741824, config["mysql"]["max_allowed_packet"]["maximum"]
        )
        self.assertEqual(
            102400, config["mysql"]["max_allowed_packet"]["minimum"]
        )
        self.assertFalse(
            config["mysql"]["max_allowed_packet"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["mysql"]["max_allowed_packet"]["type"]
        )

        self.assertEqual(
            "Limits the size of internal in-memory tables. Also set tmp_table_size. Default is 16777216 (16M)",
            config["mysql"]["max_heap_table_size"]["description"],
        )
        self.assertEqual(
            16777216, config["mysql"]["max_heap_table_size"]["example"]
        )
        self.assertEqual(
            1073741824, config["mysql"]["max_heap_table_size"]["maximum"]
        )
        self.assertEqual(
            1048576, config["mysql"]["max_heap_table_size"]["minimum"]
        )
        self.assertFalse(
            config["mysql"]["max_heap_table_size"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["mysql"]["max_heap_table_size"]["type"]
        )

        self.assertEqual(
            "Start sizes of connection buffer and result buffer. Default is 16384 (16K). Changing this parameter will lead to a restart of the MySQL service.",
            config["mysql"]["net_buffer_length"]["description"],
        )
        self.assertEqual(16384, config["mysql"]["net_buffer_length"]["example"])
        self.assertEqual(
            1048576, config["mysql"]["net_buffer_length"]["maximum"]
        )
        self.assertEqual(1024, config["mysql"]["net_buffer_length"]["minimum"])
        self.assertTrue(
            config["mysql"]["net_buffer_length"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["mysql"]["net_buffer_length"]["type"]
        )

        self.assertEqual(
            "The number of seconds to wait for more data from a connection before aborting the read.",
            config["mysql"]["net_read_timeout"]["description"],
        )
        self.assertEqual(30, config["mysql"]["net_read_timeout"]["example"])
        self.assertEqual(3600, config["mysql"]["net_read_timeout"]["maximum"])
        self.assertEqual(1, config["mysql"]["net_read_timeout"]["minimum"])
        self.assertFalse(
            config["mysql"]["net_read_timeout"]["requires_restart"]
        )
        self.assertEqual("integer", config["mysql"]["net_read_timeout"]["type"])

        self.assertEqual(
            "The number of seconds to wait for a block to be written to a connection before aborting the write.",
            config["mysql"]["net_write_timeout"]["description"],
        )
        self.assertEqual(30, config["mysql"]["net_write_timeout"]["example"])
        self.assertEqual(3600, config["mysql"]["net_write_timeout"]["maximum"])
        self.assertEqual(1, config["mysql"]["net_write_timeout"]["minimum"])
        self.assertFalse(
            config["mysql"]["net_write_timeout"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["mysql"]["net_write_timeout"]["type"]
        )

        self.assertEqual(
            "Sort buffer size in bytes for ORDER BY optimization. Default is 262144 (256K)",
            config["mysql"]["sort_buffer_size"]["description"],
        )
        self.assertEqual(262144, config["mysql"]["sort_buffer_size"]["example"])
        self.assertEqual(
            1073741824, config["mysql"]["sort_buffer_size"]["maximum"]
        )
        self.assertEqual(32768, config["mysql"]["sort_buffer_size"]["minimum"])
        self.assertFalse(
            config["mysql"]["sort_buffer_size"]["requires_restart"]
        )
        self.assertEqual("integer", config["mysql"]["sort_buffer_size"]["type"])

        self.assertEqual(
            "Global SQL mode. Set to empty to use MySQL server defaults. When creating a new service and not setting this field Akamai default SQL mode (strict, SQL standard compliant) will be assigned.",
            config["mysql"]["sql_mode"]["description"],
        )
        self.assertEqual(
            "ANSI,TRADITIONAL", config["mysql"]["sql_mode"]["example"]
        )
        self.assertEqual(1024, config["mysql"]["sql_mode"]["maxLength"])
        self.assertEqual(
            "^[A-Z_]*(,[A-Z_]+)*$", config["mysql"]["sql_mode"]["pattern"]
        )
        self.assertFalse(config["mysql"]["sql_mode"]["requires_restart"])
        self.assertEqual("string", config["mysql"]["sql_mode"]["type"])

        self.assertEqual(
            "Require primary key to be defined for new tables or old tables modified with ALTER TABLE and fail if missing. It is recommended to always have primary keys because various functionality may break if any large table is missing them.",
            config["mysql"]["sql_require_primary_key"]["description"],
        )
        self.assertTrue(config["mysql"]["sql_require_primary_key"]["example"])
        self.assertFalse(
            config["mysql"]["sql_require_primary_key"]["requires_restart"]
        )
        self.assertEqual(
            "boolean", config["mysql"]["sql_require_primary_key"]["type"]
        )

        self.assertEqual(
            "Limits the size of internal in-memory tables. Also set max_heap_table_size. Default is 16777216 (16M)",
            config["mysql"]["tmp_table_size"]["description"],
        )
        self.assertEqual(16777216, config["mysql"]["tmp_table_size"]["example"])
        self.assertEqual(
            1073741824, config["mysql"]["tmp_table_size"]["maximum"]
        )
        self.assertEqual(1048576, config["mysql"]["tmp_table_size"]["minimum"])
        self.assertFalse(config["mysql"]["tmp_table_size"]["requires_restart"])
        self.assertEqual("integer", config["mysql"]["tmp_table_size"]["type"])

        self.assertEqual(
            "The number of seconds the server waits for activity on a noninteractive connection before closing it.",
            config["mysql"]["wait_timeout"]["description"],
        )
        self.assertEqual(28800, config["mysql"]["wait_timeout"]["example"])
        self.assertEqual(2147483, config["mysql"]["wait_timeout"]["maximum"])
        self.assertEqual(1, config["mysql"]["wait_timeout"]["minimum"])
        self.assertFalse(config["mysql"]["wait_timeout"]["requires_restart"])
        self.assertEqual("integer", config["mysql"]["wait_timeout"]["type"])

        self.assertEqual(
            "The minimum amount of time in seconds to keep binlog entries before deletion. This may be extended for services that require binlog entries for longer than the default for example if using the MySQL Debezium Kafka connector.",
            config["binlog_retention_period"]["description"],
        )
        self.assertEqual(600, config["binlog_retention_period"]["example"])
        self.assertEqual(86400, config["binlog_retention_period"]["maximum"])
        self.assertEqual(600, config["binlog_retention_period"]["minimum"])
        self.assertFalse(config["binlog_retention_period"]["requires_restart"])
        self.assertEqual("integer", config["binlog_retention_period"]["type"])

    def test_postgresql_config_options(self):
        """
        Test that PostgreSQL configuration options can be retrieved
        """

        config = self.client.database.postgresql_config_options()

        self.assertEqual(
            "Specifies a fraction of the table size to add to autovacuum_analyze_threshold when "
            + "deciding whether to trigger an ANALYZE. The default is 0.2 (20% of table size)",
            config["pg"]["autovacuum_analyze_scale_factor"]["description"],
        )
        self.assertEqual(
            1.0, config["pg"]["autovacuum_analyze_scale_factor"]["maximum"]
        )
        self.assertEqual(
            0.0, config["pg"]["autovacuum_analyze_scale_factor"]["minimum"]
        )
        self.assertFalse(
            config["pg"]["autovacuum_analyze_scale_factor"]["requires_restart"]
        )
        self.assertEqual(
            "number", config["pg"]["autovacuum_analyze_scale_factor"]["type"]
        )

        self.assertEqual(
            "Specifies the minimum number of inserted, updated or deleted tuples needed to trigger an ANALYZE in any one table. The default is 50 tuples.",
            config["pg"]["autovacuum_analyze_threshold"]["description"],
        )
        self.assertEqual(
            2147483647, config["pg"]["autovacuum_analyze_threshold"]["maximum"]
        )
        self.assertEqual(
            0, config["pg"]["autovacuum_analyze_threshold"]["minimum"]
        )
        self.assertFalse(
            config["pg"]["autovacuum_analyze_threshold"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["autovacuum_analyze_threshold"]["type"]
        )

        self.assertEqual(
            "Specifies the maximum number of autovacuum processes (other than the autovacuum launcher) that may be running at any one time. The default is three. This parameter can only be set at server start.",
            config["pg"]["autovacuum_max_workers"]["description"],
        )
        self.assertEqual(20, config["pg"]["autovacuum_max_workers"]["maximum"])
        self.assertEqual(1, config["pg"]["autovacuum_max_workers"]["minimum"])
        self.assertFalse(
            config["pg"]["autovacuum_max_workers"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["autovacuum_max_workers"]["type"]
        )

        self.assertEqual(
            "Specifies the minimum delay between autovacuum runs on any given database. The delay is measured in seconds, and the default is one minute",
            config["pg"]["autovacuum_naptime"]["description"],
        )
        self.assertEqual(86400, config["pg"]["autovacuum_naptime"]["maximum"])
        self.assertEqual(1, config["pg"]["autovacuum_naptime"]["minimum"])
        self.assertFalse(config["pg"]["autovacuum_naptime"]["requires_restart"])
        self.assertEqual("integer", config["pg"]["autovacuum_naptime"]["type"])

        self.assertEqual(
            "Specifies the cost delay value that will be used in automatic VACUUM operations. If -1 is specified, the regular vacuum_cost_delay value will be used. The default value is 20 milliseconds",
            config["pg"]["autovacuum_vacuum_cost_delay"]["description"],
        )
        self.assertEqual(
            100, config["pg"]["autovacuum_vacuum_cost_delay"]["maximum"]
        )
        self.assertEqual(
            -1, config["pg"]["autovacuum_vacuum_cost_delay"]["minimum"]
        )
        self.assertFalse(
            config["pg"]["autovacuum_vacuum_cost_delay"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["autovacuum_vacuum_cost_delay"]["type"]
        )

        self.assertEqual(
            "Specifies the cost limit value that will be used in automatic VACUUM operations. If -1 is specified (which is the default), the regular vacuum_cost_limit value will be used.",
            config["pg"]["autovacuum_vacuum_cost_limit"]["description"],
        )
        self.assertEqual(
            10000, config["pg"]["autovacuum_vacuum_cost_limit"]["maximum"]
        )
        self.assertEqual(
            -1, config["pg"]["autovacuum_vacuum_cost_limit"]["minimum"]
        )
        self.assertFalse(
            config["pg"]["autovacuum_vacuum_cost_limit"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["autovacuum_vacuum_cost_limit"]["type"]
        )

        self.assertEqual(
            "Specifies a fraction of the table size to add to autovacuum_vacuum_threshold when deciding whether to trigger a VACUUM. The default is 0.2 (20% of table size)",
            config["pg"]["autovacuum_vacuum_scale_factor"]["description"],
        )
        self.assertEqual(
            1.0, config["pg"]["autovacuum_vacuum_scale_factor"]["maximum"]
        )
        self.assertEqual(
            0.0, config["pg"]["autovacuum_vacuum_scale_factor"]["minimum"]
        )
        self.assertFalse(
            config["pg"]["autovacuum_vacuum_scale_factor"]["requires_restart"]
        )
        self.assertEqual(
            "number", config["pg"]["autovacuum_vacuum_scale_factor"]["type"]
        )

        self.assertEqual(
            "Specifies the minimum number of updated or deleted tuples needed to trigger a VACUUM in any one table. The default is 50 tuples",
            config["pg"]["autovacuum_vacuum_threshold"]["description"],
        )
        self.assertEqual(
            2147483647, config["pg"]["autovacuum_vacuum_threshold"]["maximum"]
        )
        self.assertEqual(
            0, config["pg"]["autovacuum_vacuum_threshold"]["minimum"]
        )
        self.assertFalse(
            config["pg"]["autovacuum_vacuum_threshold"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["autovacuum_vacuum_threshold"]["type"]
        )

        self.assertEqual(
            "Specifies the delay between activity rounds for the background writer in milliseconds. Default is 200.",
            config["pg"]["bgwriter_delay"]["description"],
        )
        self.assertEqual(200, config["pg"]["bgwriter_delay"]["example"])
        self.assertEqual(10000, config["pg"]["bgwriter_delay"]["maximum"])
        self.assertEqual(10, config["pg"]["bgwriter_delay"]["minimum"])
        self.assertFalse(config["pg"]["bgwriter_delay"]["requires_restart"])
        self.assertEqual("integer", config["pg"]["bgwriter_delay"]["type"])

        self.assertEqual(
            "Whenever more than bgwriter_flush_after bytes have been written by the background writer, attempt to force the OS to issue these writes to the underlying storage. Specified in kilobytes, default is 512. Setting of 0 disables forced writeback.",
            config["pg"]["bgwriter_flush_after"]["description"],
        )
        self.assertEqual(512, config["pg"]["bgwriter_flush_after"]["example"])
        self.assertEqual(2048, config["pg"]["bgwriter_flush_after"]["maximum"])
        self.assertEqual(0, config["pg"]["bgwriter_flush_after"]["minimum"])
        self.assertFalse(
            config["pg"]["bgwriter_flush_after"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["bgwriter_flush_after"]["type"]
        )

        self.assertEqual(
            "In each round, no more than this many buffers will be written by the background writer. Setting this to zero disables background writing. Default is 100.",
            config["pg"]["bgwriter_lru_maxpages"]["description"],
        )
        self.assertEqual(100, config["pg"]["bgwriter_lru_maxpages"]["example"])
        self.assertEqual(
            1073741823, config["pg"]["bgwriter_lru_maxpages"]["maximum"]
        )
        self.assertEqual(0, config["pg"]["bgwriter_lru_maxpages"]["minimum"])
        self.assertFalse(
            config["pg"]["bgwriter_lru_maxpages"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["bgwriter_lru_maxpages"]["type"]
        )

        self.assertEqual(
            "The average recent need for new buffers is multiplied by bgwriter_lru_multiplier to arrive at an estimate of the number that will be needed during the next round, (up to bgwriter_lru_maxpages). 1.0 represents a “just in time” policy of writing exactly the number of buffers predicted to be needed. Larger values provide some cushion against spikes in demand, while smaller values intentionally leave writes to be done by server processes. The default is 2.0.",
            config["pg"]["bgwriter_lru_multiplier"]["description"],
        )
        self.assertEqual(
            2.0, config["pg"]["bgwriter_lru_multiplier"]["example"]
        )
        self.assertEqual(
            10.0, config["pg"]["bgwriter_lru_multiplier"]["maximum"]
        )
        self.assertEqual(
            0.0, config["pg"]["bgwriter_lru_multiplier"]["minimum"]
        )
        self.assertFalse(
            config["pg"]["bgwriter_lru_multiplier"]["requires_restart"]
        )
        self.assertEqual(
            "number", config["pg"]["bgwriter_lru_multiplier"]["type"]
        )

        self.assertEqual(
            "This is the amount of time, in milliseconds, to wait on a lock before checking to see if there is a deadlock condition.",
            config["pg"]["deadlock_timeout"]["description"],
        )
        self.assertEqual(1000, config["pg"]["deadlock_timeout"]["example"])
        self.assertEqual(1800000, config["pg"]["deadlock_timeout"]["maximum"])
        self.assertEqual(500, config["pg"]["deadlock_timeout"]["minimum"])
        self.assertFalse(config["pg"]["deadlock_timeout"]["requires_restart"])
        self.assertEqual("integer", config["pg"]["deadlock_timeout"]["type"])

        self.assertEqual(
            "Specifies the default TOAST compression method for values of compressible columns (the default is lz4).",
            config["pg"]["default_toast_compression"]["description"],
        )
        self.assertEqual(
            ["lz4", "pglz"], config["pg"]["default_toast_compression"]["enum"]
        )
        self.assertEqual(
            "lz4", config["pg"]["default_toast_compression"]["example"]
        )
        self.assertFalse(
            config["pg"]["default_toast_compression"]["requires_restart"]
        )
        self.assertEqual(
            "string", config["pg"]["default_toast_compression"]["type"]
        )

        self.assertEqual(
            "Time out sessions with open transactions after this number of milliseconds",
            config["pg"]["idle_in_transaction_session_timeout"]["description"],
        )
        self.assertEqual(
            604800000,
            config["pg"]["idle_in_transaction_session_timeout"]["maximum"],
        )
        self.assertEqual(
            0, config["pg"]["idle_in_transaction_session_timeout"]["minimum"]
        )
        self.assertFalse(
            config["pg"]["idle_in_transaction_session_timeout"][
                "requires_restart"
            ]
        )
        self.assertEqual(
            "integer",
            config["pg"]["idle_in_transaction_session_timeout"]["type"],
        )

        self.assertEqual(
            "Controls system-wide use of Just-in-Time Compilation (JIT).",
            config["pg"]["jit"]["description"],
        )
        self.assertTrue(config["pg"]["jit"]["example"])
        self.assertFalse(config["pg"]["jit"]["requires_restart"])
        self.assertEqual("boolean", config["pg"]["jit"]["type"])

        self.assertEqual(
            "PostgreSQL maximum number of files that can be open per process",
            config["pg"]["max_files_per_process"]["description"],
        )
        self.assertEqual(4096, config["pg"]["max_files_per_process"]["maximum"])
        self.assertEqual(1000, config["pg"]["max_files_per_process"]["minimum"])
        self.assertFalse(
            config["pg"]["max_files_per_process"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["max_files_per_process"]["type"]
        )

        self.assertEqual(
            "PostgreSQL maximum locks per transaction",
            config["pg"]["max_locks_per_transaction"]["description"],
        )
        self.assertEqual(
            6400, config["pg"]["max_locks_per_transaction"]["maximum"]
        )
        self.assertEqual(
            64, config["pg"]["max_locks_per_transaction"]["minimum"]
        )
        self.assertFalse(
            config["pg"]["max_locks_per_transaction"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["max_locks_per_transaction"]["type"]
        )

        self.assertEqual(
            "PostgreSQL maximum logical replication workers (taken from the pool of max_parallel_workers)",
            config["pg"]["max_logical_replication_workers"]["description"],
        )
        self.assertEqual(
            64, config["pg"]["max_logical_replication_workers"]["maximum"]
        )
        self.assertEqual(
            4, config["pg"]["max_logical_replication_workers"]["minimum"]
        )
        self.assertFalse(
            config["pg"]["max_logical_replication_workers"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["max_logical_replication_workers"]["type"]
        )

        self.assertEqual(
            "Sets the maximum number of workers that the system can support for parallel queries",
            config["pg"]["max_parallel_workers"]["description"],
        )
        self.assertEqual(96, config["pg"]["max_parallel_workers"]["maximum"])
        self.assertEqual(0, config["pg"]["max_parallel_workers"]["minimum"])
        self.assertFalse(
            config["pg"]["max_parallel_workers"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["max_parallel_workers"]["type"]
        )

        self.assertEqual(
            "Sets the maximum number of workers that can be started by a single Gather or Gather Merge node",
            config["pg"]["max_parallel_workers_per_gather"]["description"],
        )
        self.assertEqual(
            96, config["pg"]["max_parallel_workers_per_gather"]["maximum"]
        )
        self.assertEqual(
            0, config["pg"]["max_parallel_workers_per_gather"]["minimum"]
        )
        self.assertFalse(
            config["pg"]["max_parallel_workers_per_gather"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["max_parallel_workers_per_gather"]["type"]
        )

        self.assertEqual(
            "PostgreSQL maximum predicate locks per transaction",
            config["pg"]["max_pred_locks_per_transaction"]["description"],
        )
        self.assertEqual(
            5120, config["pg"]["max_pred_locks_per_transaction"]["maximum"]
        )
        self.assertEqual(
            64, config["pg"]["max_pred_locks_per_transaction"]["minimum"]
        )
        self.assertFalse(
            config["pg"]["max_pred_locks_per_transaction"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["max_pred_locks_per_transaction"]["type"]
        )

        self.assertEqual(
            "PostgreSQL maximum replication slots",
            config["pg"]["max_replication_slots"]["description"],
        )
        self.assertEqual(64, config["pg"]["max_replication_slots"]["maximum"])
        self.assertEqual(8, config["pg"]["max_replication_slots"]["minimum"])
        self.assertFalse(
            config["pg"]["max_replication_slots"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["max_replication_slots"]["type"]
        )

        self.assertEqual(
            "PostgreSQL maximum WAL size (MB) reserved for replication slots. Default is -1 (unlimited). wal_keep_size minimum WAL size setting takes precedence over this.",
            config["pg"]["max_slot_wal_keep_size"]["description"],
        )
        self.assertEqual(
            2147483647, config["pg"]["max_slot_wal_keep_size"]["maximum"]
        )
        self.assertEqual(-1, config["pg"]["max_slot_wal_keep_size"]["minimum"])
        self.assertFalse(
            config["pg"]["max_slot_wal_keep_size"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["max_slot_wal_keep_size"]["type"]
        )

        self.assertEqual(
            "Maximum depth of the stack in bytes",
            config["pg"]["max_stack_depth"]["description"],
        )
        self.assertEqual(6291456, config["pg"]["max_stack_depth"]["maximum"])
        self.assertEqual(2097152, config["pg"]["max_stack_depth"]["minimum"])
        self.assertFalse(config["pg"]["max_stack_depth"]["requires_restart"])
        self.assertEqual("integer", config["pg"]["max_stack_depth"]["type"])

        self.assertEqual(
            "Max standby archive delay in milliseconds",
            config["pg"]["max_standby_archive_delay"]["description"],
        )
        self.assertEqual(
            43200000, config["pg"]["max_standby_archive_delay"]["maximum"]
        )
        self.assertEqual(
            1, config["pg"]["max_standby_archive_delay"]["minimum"]
        )
        self.assertFalse(
            config["pg"]["max_standby_archive_delay"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["max_standby_archive_delay"]["type"]
        )

        self.assertEqual(
            "Max standby streaming delay in milliseconds",
            config["pg"]["max_standby_streaming_delay"]["description"],
        )
        self.assertEqual(
            43200000, config["pg"]["max_standby_streaming_delay"]["maximum"]
        )
        self.assertEqual(
            1, config["pg"]["max_standby_streaming_delay"]["minimum"]
        )
        self.assertFalse(
            config["pg"]["max_standby_streaming_delay"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["max_standby_streaming_delay"]["type"]
        )

        self.assertEqual(
            "PostgreSQL maximum WAL senders",
            config["pg"]["max_wal_senders"]["description"],
        )
        self.assertEqual(64, config["pg"]["max_wal_senders"]["maximum"])
        self.assertEqual(20, config["pg"]["max_wal_senders"]["minimum"])
        self.assertFalse(config["pg"]["max_wal_senders"]["requires_restart"])
        self.assertEqual("integer", config["pg"]["max_wal_senders"]["type"])

        self.assertEqual(
            "Sets the maximum number of background processes that the system can support",
            config["pg"]["max_worker_processes"]["description"],
        )
        self.assertEqual(96, config["pg"]["max_worker_processes"]["maximum"])
        self.assertEqual(8, config["pg"]["max_worker_processes"]["minimum"])
        self.assertFalse(
            config["pg"]["max_worker_processes"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["max_worker_processes"]["type"]
        )

        self.assertEqual(
            "Chooses the algorithm for encrypting passwords.",
            config["pg"]["password_encryption"]["description"],
        )
        self.assertEqual(
            ["md5", "scram-sha-256"],
            config["pg"]["password_encryption"]["enum"],
        )
        self.assertEqual(
            "scram-sha-256", config["pg"]["password_encryption"]["example"]
        )
        self.assertFalse(
            config["pg"]["password_encryption"]["requires_restart"]
        )
        self.assertEqual(
            ["string", "null"], config["pg"]["password_encryption"]["type"]
        )

        self.assertEqual(
            "Sets the time interval to run pg_partman's scheduled tasks",
            config["pg"]["pg_partman_bgw.interval"]["description"],
        )
        self.assertEqual(
            3600, config["pg"]["pg_partman_bgw.interval"]["example"]
        )
        self.assertEqual(
            604800, config["pg"]["pg_partman_bgw.interval"]["maximum"]
        )
        self.assertEqual(
            3600, config["pg"]["pg_partman_bgw.interval"]["minimum"]
        )
        self.assertFalse(
            config["pg"]["pg_partman_bgw.interval"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["pg_partman_bgw.interval"]["type"]
        )

        self.assertEqual(
            "Controls which role to use for pg_partman's scheduled background tasks.",
            config["pg"]["pg_partman_bgw.role"]["description"],
        )
        self.assertEqual(
            "myrolename", config["pg"]["pg_partman_bgw.role"]["example"]
        )
        self.assertEqual(64, config["pg"]["pg_partman_bgw.role"]["maxLength"])
        self.assertEqual(
            "^[_A-Za-z0-9][-._A-Za-z0-9]{0,63}$",
            config["pg"]["pg_partman_bgw.role"]["pattern"],
        )
        self.assertFalse(
            config["pg"]["pg_partman_bgw.role"]["requires_restart"]
        )
        self.assertEqual("string", config["pg"]["pg_partman_bgw.role"]["type"])

        self.assertEqual(
            "Enables or disables query plan monitoring",
            config["pg"]["pg_stat_monitor.pgsm_enable_query_plan"][
                "description"
            ],
        )
        self.assertFalse(
            config["pg"]["pg_stat_monitor.pgsm_enable_query_plan"]["example"]
        )
        self.assertFalse(
            config["pg"]["pg_stat_monitor.pgsm_enable_query_plan"][
                "requires_restart"
            ]
        )
        self.assertEqual(
            "boolean",
            config["pg"]["pg_stat_monitor.pgsm_enable_query_plan"]["type"],
        )

        self.assertEqual(
            "Sets the maximum number of buckets",
            config["pg"]["pg_stat_monitor.pgsm_max_buckets"]["description"],
        )
        self.assertEqual(
            10, config["pg"]["pg_stat_monitor.pgsm_max_buckets"]["example"]
        )
        self.assertEqual(
            10, config["pg"]["pg_stat_monitor.pgsm_max_buckets"]["maximum"]
        )
        self.assertEqual(
            1, config["pg"]["pg_stat_monitor.pgsm_max_buckets"]["minimum"]
        )
        self.assertFalse(
            config["pg"]["pg_stat_monitor.pgsm_max_buckets"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["pg_stat_monitor.pgsm_max_buckets"]["type"]
        )

        self.assertEqual(
            "Controls which statements are counted. Specify top to track top-level statements (those issued directly by clients), all to also track nested statements (such as statements invoked within functions), or none to disable statement statistics collection. The default value is top.",
            config["pg"]["pg_stat_statements.track"]["description"],
        )
        self.assertEqual(
            ["all", "top", "none"],
            config["pg"]["pg_stat_statements.track"]["enum"],
        )
        self.assertFalse(
            config["pg"]["pg_stat_statements.track"]["requires_restart"]
        )
        self.assertEqual(
            ["string"], config["pg"]["pg_stat_statements.track"]["type"]
        )

        self.assertEqual(
            "PostgreSQL temporary file limit in KiB, -1 for unlimited",
            config["pg"]["temp_file_limit"]["description"],
        )
        self.assertEqual(5000000, config["pg"]["temp_file_limit"]["example"])
        self.assertEqual(2147483647, config["pg"]["temp_file_limit"]["maximum"])
        self.assertEqual(-1, config["pg"]["temp_file_limit"]["minimum"])
        self.assertFalse(config["pg"]["temp_file_limit"]["requires_restart"])
        self.assertEqual("integer", config["pg"]["temp_file_limit"]["type"])

        self.assertEqual(
            "PostgreSQL service timezone",
            config["pg"]["timezone"]["description"],
        )
        self.assertEqual("Europe/Helsinki", config["pg"]["timezone"]["example"])
        self.assertEqual(64, config["pg"]["timezone"]["maxLength"])
        self.assertEqual("^[\\w/]*$", config["pg"]["timezone"]["pattern"])
        self.assertFalse(config["pg"]["timezone"]["requires_restart"])
        self.assertEqual("string", config["pg"]["timezone"]["type"])

        self.assertEqual(
            "Specifies the number of bytes reserved to track the currently executing command for each active session.",
            config["pg"]["track_activity_query_size"]["description"],
        )
        self.assertEqual(
            1024, config["pg"]["track_activity_query_size"]["example"]
        )
        self.assertEqual(
            10240, config["pg"]["track_activity_query_size"]["maximum"]
        )
        self.assertEqual(
            1024, config["pg"]["track_activity_query_size"]["minimum"]
        )
        self.assertFalse(
            config["pg"]["track_activity_query_size"]["requires_restart"]
        )
        self.assertEqual(
            "integer", config["pg"]["track_activity_query_size"]["type"]
        )

        self.assertEqual(
            "Record commit time of transactions.",
            config["pg"]["track_commit_timestamp"]["description"],
        )
        self.assertEqual(
            "off", config["pg"]["track_commit_timestamp"]["example"]
        )
        self.assertEqual(
            ["off", "on"], config["pg"]["track_commit_timestamp"]["enum"]
        )
        self.assertFalse(
            config["pg"]["track_commit_timestamp"]["requires_restart"]
        )
        self.assertEqual(
            "string", config["pg"]["track_commit_timestamp"]["type"]
        )

        self.assertEqual(
            "Enables tracking of function call counts and time used.",
            config["pg"]["track_functions"]["description"],
        )
        self.assertEqual(
            ["all", "pl", "none"], config["pg"]["track_functions"]["enum"]
        )
        self.assertFalse(config["pg"]["track_functions"]["requires_restart"])
        self.assertEqual("string", config["pg"]["track_functions"]["type"])

        self.assertEqual(
            "Enables timing of database I/O calls. This parameter is off by default, because it will repeatedly query the operating system for the current time, which may cause significant overhead on some platforms.",
            config["pg"]["track_io_timing"]["description"],
        )
        self.assertEqual("off", config["pg"]["track_io_timing"]["example"])
        self.assertEqual(["off", "on"], config["pg"]["track_io_timing"]["enum"])
        self.assertFalse(config["pg"]["track_io_timing"]["requires_restart"])
        self.assertEqual("string", config["pg"]["track_io_timing"]["type"])

        self.assertEqual(
            "Terminate replication connections that are inactive for longer than this amount of time, in milliseconds. Setting this value to zero disables the timeout.",
            config["pg"]["wal_sender_timeout"]["description"],
        )
        self.assertEqual(60000, config["pg"]["wal_sender_timeout"]["example"])
        self.assertFalse(config["pg"]["wal_sender_timeout"]["requires_restart"])
        self.assertEqual("integer", config["pg"]["wal_sender_timeout"]["type"])

        self.assertEqual(
            "WAL flush interval in milliseconds. Note that setting this value to lower than the default 200ms may negatively impact performance",
            config["pg"]["wal_writer_delay"]["description"],
        )
        self.assertEqual(50, config["pg"]["wal_writer_delay"]["example"])
        self.assertEqual(200, config["pg"]["wal_writer_delay"]["maximum"])
        self.assertEqual(10, config["pg"]["wal_writer_delay"]["minimum"])
        self.assertFalse(config["pg"]["wal_writer_delay"]["requires_restart"])
        self.assertEqual("integer", config["pg"]["wal_writer_delay"]["type"])

        self.assertEqual(
            "Enable the pg_stat_monitor extension. Enabling this extension will cause the cluster to be restarted. When this extension is enabled, pg_stat_statements results for utility commands are unreliable",
            config["pg_stat_monitor_enable"]["description"],
        )
        self.assertTrue(config["pg_stat_monitor_enable"]["requires_restart"])
        self.assertEqual("boolean", config["pg_stat_monitor_enable"]["type"])

        self.assertEqual(
            "Number of seconds of master unavailability before triggering database failover to standby",
            config["pglookout"]["max_failover_replication_time_lag"][
                "description"
            ],
        )
        self.assertEqual(
            int(9223372036854775000),
            config["pglookout"]["max_failover_replication_time_lag"]["maximum"],
        )
        self.assertEqual(
            int(10),
            config["pglookout"]["max_failover_replication_time_lag"]["minimum"],
        )
        self.assertFalse(
            config["pglookout"]["max_failover_replication_time_lag"][
                "requires_restart"
            ]
        )
        self.assertEqual(
            "integer",
            config["pglookout"]["max_failover_replication_time_lag"]["type"],
        )

        self.assertEqual(
            "Percentage of total RAM that the database server uses for shared memory buffers. Valid range is 20-60 (float), which corresponds to 20% - 60%. This setting adjusts the shared_buffers configuration value.",
            config["shared_buffers_percentage"]["description"],
        )
        self.assertEqual(41.5, config["shared_buffers_percentage"]["example"])
        self.assertEqual(60.0, config["shared_buffers_percentage"]["maximum"])
        self.assertEqual(20.0, config["shared_buffers_percentage"]["minimum"])
        self.assertFalse(
            config["shared_buffers_percentage"]["requires_restart"]
        )
        self.assertEqual("number", config["shared_buffers_percentage"]["type"])

        self.assertEqual(
            "Sets the maximum amount of memory to be used by a query operation (such as a sort or hash table) before writing to temporary disk files, in MB. Default is 1MB + 0.075% of total RAM (up to 32MB).",
            config["work_mem"]["description"],
        )
        self.assertEqual(4, config["work_mem"]["example"])
        self.assertEqual(1024, config["work_mem"]["maximum"])
        self.assertEqual(1, config["work_mem"]["minimum"])
        self.assertFalse(config["work_mem"]["requires_restart"])
        self.assertEqual("integer", config["work_mem"]["type"])

    def test_get_mysql_instances(self):
        """
        Test that mysql instances can be retrieved properly
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

    def test_get_postgresql_instances(self):
        """
        Test that postgresql instances can be retrieved properly
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

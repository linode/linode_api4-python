from linode_api4 import LinodeClient
from linode_api4.objects import (
    MySQLDatabase,
    MySQLDatabaseConfigMySQLOptions,
    MySQLDatabaseConfigOptions,
    PostgreSQLDatabase,
    PostgreSQLDatabaseConfigOptions,
    PostgreSQLDatabaseConfigPGOptions,
)


# Test Helpers
def get_db_engine_id(client: LinodeClient, engine: str):
    engines = client.database.engines()
    engine_id = ""
    for e in engines:
        if e.engine == engine:
            engine_id = e.id

    return str(engine_id)


def get_sql_db_status(client: LinodeClient, db_id, status: str):
    db = client.load(MySQLDatabase, db_id)
    return db.status == status


def get_postgres_db_status(client: LinodeClient, db_id, status: str):
    db = client.load(PostgreSQLDatabase, db_id)
    return db.status == status


def make_full_mysql_engine_config():
    return MySQLDatabaseConfigOptions(
        binlog_retention_period=600,
        mysql=MySQLDatabaseConfigMySQLOptions(
            connect_timeout=20,
            default_time_zone="+00:00",
            group_concat_max_len=1024,
            information_schema_stats_expiry=900,
            innodb_change_buffer_max_size=25,
            innodb_flush_neighbors=1,
            innodb_ft_min_token_size=3,
            innodb_ft_server_stopword_table="db_name/table_name",
            innodb_lock_wait_timeout=50,
            innodb_log_buffer_size=16777216,
            innodb_online_alter_log_max_size=134217728,
            innodb_read_io_threads=4,
            innodb_rollback_on_timeout=True,
            innodb_thread_concurrency=8,
            innodb_write_io_threads=4,
            interactive_timeout=300,
            internal_tmp_mem_storage_engine="TempTable",
            max_allowed_packet=67108864,
            max_heap_table_size=16777216,
            net_buffer_length=16384,
            net_read_timeout=30,
            net_write_timeout=60,
            sort_buffer_size=262144,
            sql_mode="TRADITIONAL",
            sql_require_primary_key=False,
            tmp_table_size=16777216,
            wait_timeout=28800,
        ),
    )


def make_mysql_engine_config_w_nullable_field():
    return MySQLDatabaseConfigOptions(
        mysql=MySQLDatabaseConfigMySQLOptions(
            innodb_ft_server_stopword_table=None,
        ),
    )


def make_full_postgres_engine_config():
    return PostgreSQLDatabaseConfigOptions(
        pg=PostgreSQLDatabaseConfigPGOptions(
            autovacuum_analyze_scale_factor=0.1,
            autovacuum_analyze_threshold=50,
            autovacuum_max_workers=3,
            autovacuum_naptime=60,
            autovacuum_vacuum_cost_delay=20,
            autovacuum_vacuum_cost_limit=200,
            autovacuum_vacuum_scale_factor=0.2,
            autovacuum_vacuum_threshold=50,
            bgwriter_delay=200,
            bgwriter_flush_after=64,
            bgwriter_lru_maxpages=100,
            bgwriter_lru_multiplier=2.0,
            deadlock_timeout=1000,
            default_toast_compression="lz4",
            idle_in_transaction_session_timeout=600000,
            jit=True,
            max_files_per_process=1000,
            max_locks_per_transaction=64,
            max_logical_replication_workers=4,
            max_parallel_workers=4,
            max_parallel_workers_per_gather=2,
            max_pred_locks_per_transaction=64,
            max_replication_slots=10,
            max_slot_wal_keep_size=2048,
            max_stack_depth=6291456,
            max_standby_archive_delay=30000,
            max_standby_streaming_delay=30000,
            max_wal_senders=20,
            max_worker_processes=8,
            password_encryption="scram-sha-256",
            temp_file_limit=1,
            timezone="UTC",
            track_activity_query_size=2048,
            track_functions="all",
            wal_sender_timeout=60000,
            wal_writer_delay=200,
            pg_partman_bgw_interval=3600,
            pg_partman_bgw_role="myrolename",
            pg_stat_monitor_pgsm_enable_query_plan=True,
            pg_stat_monitor_pgsm_max_buckets=2,
            pg_stat_statements_track="top",
        ),
        pg_stat_monitor_enable=True,
        shared_buffers_percentage=25.0,
        work_mem=1024,
    )


def make_postgres_engine_config_w_password_encryption_null():
    return PostgreSQLDatabaseConfigOptions(
        pg=PostgreSQLDatabaseConfigPGOptions(
            password_encryption=None,
        ),
    )

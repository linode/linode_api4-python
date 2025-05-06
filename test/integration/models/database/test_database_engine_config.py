import os
from test.integration.helpers import (
    get_test_label,
    send_request_when_resource_available,
    wait_for_condition,
)
from test.integration.models.database.helpers import (
    get_db_engine_id,
    get_postgres_db_status,
    get_sql_db_status,
    make_full_mysql_engine_config,
    make_full_postgres_engine_config,
    make_mysql_engine_config_w_nullable_field,
    make_postgres_engine_config_w_password_encryption_null,
)

import pytest

from linode_api4.errors import ApiError
from linode_api4.objects import (
    MySQLDatabase,
    MySQLDatabaseConfigMySQLOptions,
    MySQLDatabaseConfigOptions,
    PostgreSQLDatabase,
    PostgreSQLDatabaseConfigOptions,
    PostgreSQLDatabaseConfigPGOptions,
)


@pytest.fixture(scope="session")
def mysql_db_with_engine_config(test_linode_client):
    client = test_linode_client
    label = get_test_label() + "-sqldb"
    region = "us-ord"
    engine_id = get_db_engine_id(client, "mysql")
    dbtype = "g6-standard-1"

    db = client.database.mysql_create(
        label=label,
        region=region,
        engine=engine_id,
        ltype=dbtype,
        cluster_size=None,
        engine_config=make_full_mysql_engine_config(),
    )

    def get_db_status():
        return db.status == "active"

    # Usually take 10-15m to provision
    wait_for_condition(60, 2000, get_db_status)

    yield db

    send_request_when_resource_available(300, db.delete)


@pytest.fixture(scope="session")
def postgres_db_with_engine_config(test_linode_client):
    client = test_linode_client
    label = get_test_label() + "-postgresqldb"
    region = "us-ord"
    engine_id = "postgresql/17"
    dbtype = "g6-standard-1"

    db = client.database.postgresql_create(
        label=label,
        region=region,
        engine=engine_id,
        ltype=dbtype,
        cluster_size=None,
        engine_config=make_full_postgres_engine_config(),
    )

    def get_db_status():
        return db.status == "active"

    # Usually take 10-15m to provision
    wait_for_condition(60, 2000, get_db_status)

    yield db

    send_request_when_resource_available(300, db.delete)


# MYSQL
@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_get_mysql_config(test_linode_client):
    config = test_linode_client.database.mysql_config_options()

    # Top-level keys
    assert "binlog_retention_period" in config
    assert "mysql" in config

    # binlog_retention_period checks
    brp = config["binlog_retention_period"]
    assert isinstance(brp, dict)
    assert brp["type"] == "integer"
    assert brp["minimum"] == 600
    assert brp["maximum"] == 86400
    assert brp["requires_restart"] is False

    # mysql sub-keys
    mysql = config["mysql"]

    # mysql valid fields
    expected_keys = [
        "connect_timeout",
        "default_time_zone",
        "group_concat_max_len",
        "information_schema_stats_expiry",
        "innodb_change_buffer_max_size",
        "innodb_flush_neighbors",
        "innodb_ft_min_token_size",
        "innodb_ft_server_stopword_table",
        "innodb_lock_wait_timeout",
        "innodb_log_buffer_size",
        "innodb_online_alter_log_max_size",
        "innodb_read_io_threads",
        "innodb_rollback_on_timeout",
        "innodb_thread_concurrency",
        "innodb_write_io_threads",
        "interactive_timeout",
        "internal_tmp_mem_storage_engine",
        "max_allowed_packet",
        "max_heap_table_size",
        "net_buffer_length",
        "net_read_timeout",
        "net_write_timeout",
        "sort_buffer_size",
        "sql_mode",
        "sql_require_primary_key",
        "tmp_table_size",
        "wait_timeout",
    ]

    # Assert all valid fields are present
    for key in expected_keys:
        assert key in mysql, f"{key} not found in mysql config"

    assert mysql["connect_timeout"]["type"] == "integer"
    assert mysql["default_time_zone"]["type"] == "string"
    assert mysql["innodb_rollback_on_timeout"]["type"] == "boolean"
    assert "enum" in mysql["internal_tmp_mem_storage_engine"]
    assert "pattern" in mysql["sql_mode"]


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_create_mysql_with_engine_config(mysql_db_with_engine_config):
    db = mysql_db_with_engine_config
    actual_config = db.engine_config.mysql
    expected_config = make_full_mysql_engine_config().mysql.__dict__

    for key, expected_value in expected_config.items():
        actual_value = getattr(actual_config, key)
        assert (
            actual_value == expected_value
        ), f"{key} mismatch: expected {expected_value}, got {actual_value}"


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_update_mysql_engine_config(
    test_linode_client, mysql_db_with_engine_config
):
    db = mysql_db_with_engine_config

    db.updates.day_of_week = 2
    db.engine_config = MySQLDatabaseConfigOptions(
        mysql=MySQLDatabaseConfigMySQLOptions(connect_timeout=50),
        binlog_retention_period=880,
    )

    db.save()

    wait_for_condition(
        30,
        300,
        get_sql_db_status,
        test_linode_client,
        db.id,
        "active",
    )

    database = test_linode_client.load(MySQLDatabase, db.id)

    assert database.updates.day_of_week == 2
    assert database.engine_config.mysql.connect_timeout == 50
    assert database.engine_config.binlog_retention_period == 880


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_list_mysql_engine_config(
    test_linode_client, mysql_db_with_engine_config
):
    dbs = test_linode_client.database.mysql_instances()

    db_ids = [db.id for db in dbs]

    assert mysql_db_with_engine_config.id in db_ids


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_get_mysql_engine_config(
    test_linode_client, mysql_db_with_engine_config
):
    db = test_linode_client.load(MySQLDatabase, mysql_db_with_engine_config.id)

    assert isinstance(db, MySQLDatabase)


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_create_mysql_db_nullable_field(test_linode_client):
    client = test_linode_client
    label = get_test_label(5) + "-sqldb"
    region = "us-ord"
    engine_id = get_db_engine_id(client, "mysql")
    dbtype = "g6-standard-1"

    db = client.database.mysql_create(
        label=label,
        region=region,
        engine=engine_id,
        ltype=dbtype,
        cluster_size=None,
        engine_config=make_mysql_engine_config_w_nullable_field(),
    )

    assert db.engine_config.mysql.innodb_ft_server_stopword_table is None

    send_request_when_resource_available(300, db.delete)


# POSTGRESQL
@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_get_postgres_config(test_linode_client):
    config = test_linode_client.database.postgresql_config_options()

    # Top-level keys and structure
    assert "pg" in config

    assert "pg_stat_monitor_enable" in config
    assert config["pg_stat_monitor_enable"]["type"] == "boolean"

    assert "shared_buffers_percentage" in config
    assert config["shared_buffers_percentage"]["type"] == "number"
    assert config["shared_buffers_percentage"]["minimum"] >= 1

    assert "work_mem" in config
    assert config["work_mem"]["type"] == "integer"
    assert "minimum" in config["work_mem"]

    pg = config["pg"]

    # postgres valid fields
    expected_keys = [
        "autovacuum_analyze_scale_factor",
        "autovacuum_analyze_threshold",
        "autovacuum_max_workers",
        "autovacuum_naptime",
        "autovacuum_vacuum_cost_delay",
        "autovacuum_vacuum_cost_limit",
        "autovacuum_vacuum_scale_factor",
        "autovacuum_vacuum_threshold",
        "bgwriter_delay",
        "bgwriter_flush_after",
        "bgwriter_lru_maxpages",
        "bgwriter_lru_multiplier",
        "deadlock_timeout",
        "default_toast_compression",
        "idle_in_transaction_session_timeout",
        "jit",
        "max_files_per_process",
        "max_locks_per_transaction",
        "max_logical_replication_workers",
        "max_parallel_workers",
        "max_parallel_workers_per_gather",
        "max_pred_locks_per_transaction",
        "max_replication_slots",
        "max_slot_wal_keep_size",
        "max_stack_depth",
        "max_standby_archive_delay",
        "max_standby_streaming_delay",
        "max_wal_senders",
        "max_worker_processes",
        "password_encryption",
        "pg_partman_bgw.interval",
        "pg_partman_bgw.role",
        "pg_stat_monitor.pgsm_enable_query_plan",
        "pg_stat_monitor.pgsm_max_buckets",
        "pg_stat_statements.track",
        "temp_file_limit",
        "timezone",
        "track_activity_query_size",
        "track_commit_timestamp",
        "track_functions",
        "track_io_timing",
        "wal_sender_timeout",
        "wal_writer_delay",
    ]

    # Assert all valid fields are present
    for key in expected_keys:
        assert key in pg, f"{key} not found in postgresql config"

    assert pg["autovacuum_analyze_scale_factor"]["type"] == "number"
    assert pg["autovacuum_analyze_threshold"]["type"] == "integer"
    assert pg["autovacuum_max_workers"]["requires_restart"] is True
    assert pg["default_toast_compression"]["enum"] == ["lz4", "pglz"]
    assert pg["jit"]["type"] == "boolean"
    assert "enum" in pg["password_encryption"]
    assert "pattern" in pg["pg_partman_bgw.role"]
    assert pg["pg_stat_monitor.pgsm_enable_query_plan"]["type"] == "boolean"
    assert pg["pg_stat_monitor.pgsm_max_buckets"]["requires_restart"] is True
    assert pg["pg_stat_statements.track"]["enum"] == ["all", "top", "none"]
    assert pg["track_commit_timestamp"]["enum"] == ["off", "on"]
    assert pg["track_functions"]["enum"] == ["all", "pl", "none"]
    assert pg["track_io_timing"]["enum"] == ["off", "on"]


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_create_postgres_with_engine_config(
    test_linode_client, postgres_db_with_engine_config
):
    db = postgres_db_with_engine_config
    actual_config = db.engine_config.pg
    expected_config = make_full_postgres_engine_config().pg.__dict__

    for key, expected_value in expected_config.items():
        actual_value = getattr(actual_config, key, None)
        assert (
            actual_value is None or actual_value == expected_value
        ), f"{key} mismatch: expected {expected_value}, got {actual_value}"


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_update_postgres_engine_config(
    test_linode_client, postgres_db_with_engine_config
):
    db = postgres_db_with_engine_config

    db.updates.day_of_week = 2
    db.engine_config = PostgreSQLDatabaseConfigOptions(
        pg=PostgreSQLDatabaseConfigPGOptions(
            autovacuum_analyze_threshold=70, deadlock_timeout=2000
        ),
        shared_buffers_percentage=25.0,
    )

    db.save()

    wait_for_condition(
        30,
        300,
        get_postgres_db_status,
        test_linode_client,
        db.id,
        "active",
    )

    database = test_linode_client.load(PostgreSQLDatabase, db.id)

    assert database.updates.day_of_week == 2
    assert database.engine_config.pg.autovacuum_analyze_threshold == 70
    assert database.engine_config.pg.deadlock_timeout == 2000
    assert database.engine_config.shared_buffers_percentage == 25.0


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_create_pg13_with_lz4_error(test_linode_client):
    client = test_linode_client
    label = get_test_label() + "-postgresqldb"
    region = "us-ord"
    engine_id = get_db_engine_id(client, "postgresql/13")
    dbtype = "g6-standard-1"

    try:
        client.database.postgresql_create(
            label=label,
            region=region,
            engine=engine_id,
            ltype=dbtype,
            cluster_size=None,
            engine_config=PostgreSQLDatabaseConfigOptions(
                pg=PostgreSQLDatabaseConfigPGOptions(
                    default_toast_compression="lz4"
                ),
                work_mem=4,
            ),
        )
    except ApiError as e:
        assert "An error occurred" in str(e.json)
        assert e.status == 500


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_list_postgres_engine_config(
    test_linode_client, postgres_db_with_engine_config
):
    dbs = test_linode_client.database.postgresql_instances()

    db_ids = [db.id for db in dbs]

    assert postgres_db_with_engine_config.id in db_ids


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_get_postgres_engine_config(
    test_linode_client, postgres_db_with_engine_config
):
    db = test_linode_client.load(
        PostgreSQLDatabase, postgres_db_with_engine_config.id
    )

    assert isinstance(db, PostgreSQLDatabase)


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_create_postgres_db_password_encryption_default_md5(test_linode_client):
    client = test_linode_client
    label = get_test_label() + "-postgresqldb"
    region = "us-ord"
    engine_id = "postgresql/17"
    dbtype = "g6-standard-1"

    db = client.database.postgresql_create(
        label=label,
        region=region,
        engine=engine_id,
        ltype=dbtype,
        cluster_size=None,
        engine_config=make_postgres_engine_config_w_password_encryption_null(),
    )

    assert db.engine_config.pg.password_encryption == "md5"

    send_request_when_resource_available(300, db.delete)

import os
import time
from test.integration.helpers import (
    get_test_label,
    send_request_when_resource_available,
    wait_for_condition,
)
from test.integration.models.database.helpers import (
    get_db_engine_id,
    get_postgres_db_status,
    get_sql_db_status,
)

import pytest

from linode_api4.objects import MySQLDatabase, PostgreSQLDatabase


@pytest.fixture(scope="session")
def test_create_sql_db(test_linode_client):
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
    )

    def get_db_status():
        return db.status == "active"

    # TAKES 15-30 MINUTES TO FULLY PROVISION DB
    wait_for_condition(60, 2000, get_db_status)

    yield db

    send_request_when_resource_available(300, db.delete)


@pytest.fixture(scope="session")
def test_create_postgres_db(test_linode_client):
    client = test_linode_client
    label = get_test_label() + "-postgresqldb"
    region = "us-ord"
    engine_id = get_db_engine_id(client, "postgresql")
    dbtype = "g6-standard-1"

    db = client.database.postgresql_create(
        label=label,
        region=region,
        engine=engine_id,
        ltype=dbtype,
        cluster_size=None,
    )

    def get_db_status():
        return db.status == "active"

    # TAKES 15-30 MINUTES TO FULLY PROVISION DB
    wait_for_condition(60, 2000, get_db_status)

    yield db

    send_request_when_resource_available(300, db.delete)


@pytest.mark.skipif(
    os.getenv("RUN_DB_FORK_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_FORK_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_fork_sql_db(test_linode_client, test_create_sql_db):
    client = test_linode_client
    db_fork = client.database.mysql_fork(
        test_create_sql_db.id, test_create_sql_db.updated
    )

    def get_db_fork_status():
        return db_fork.status == "active"

    # TAKES 15-30 MINUTES TO FULLY PROVISION DB
    wait_for_condition(60, 2000, get_db_fork_status)

    assert db_fork.fork.source == test_create_sql_db.id

    db_fork.delete()


@pytest.mark.skipif(
    os.getenv("RUN_DB_FORK_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_FORK_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_fork_postgres_db(test_linode_client, test_create_postgres_db):
    client = test_linode_client
    db_fork = client.database.postgresql_fork(
        test_create_postgres_db.id, test_create_postgres_db.updated
    )

    def get_db_fork_status():
        return db_fork.status == "active"

    # TAKES 15-30 MINUTES TO FULLY PROVISION DB
    wait_for_condition(60, 2000, get_db_fork_status)

    assert db_fork.fork.source == test_create_postgres_db.id

    db_fork.delete()


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_get_types(test_linode_client):
    client = test_linode_client
    types = client.database.types()

    assert "nanode" in types[0].type_class
    assert "g6-nanode-1" in types[0].id


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_get_engines(test_linode_client):
    client = test_linode_client
    engines = client.database.engines()

    for e in engines:
        assert e.engine in ["mysql", "postgresql"]
        # assert re.search("[0-9]+.[0-9]+", e.version)
        assert e.id == e.engine + "/" + e.version


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_database_instance(test_linode_client, test_create_sql_db):
    dbs = test_linode_client.database.mysql_instances()

    assert str(test_create_sql_db.id) in str(dbs.lists)


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_mysql_suspend_resume(test_linode_client, test_create_sql_db):
    db = test_linode_client.load(MySQLDatabase, test_create_sql_db.id)

    db.suspend()

    wait_for_condition(
        10,
        300,
        get_sql_db_status,
        test_linode_client,
        test_create_sql_db.id,
        "suspended",
    )

    assert db.status == "suspended"

    db.resume()

    wait_for_condition(
        30,
        600,
        get_sql_db_status,
        test_linode_client,
        test_create_sql_db.id,
        "active",
    )

    assert db.status == "active"


# ------- POSTGRESQL DB Test cases -------
@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_get_sql_db_instance(test_linode_client, test_create_sql_db):
    dbs = test_linode_client.database.mysql_instances()
    database = ""
    for db in dbs:
        if db.id == test_create_sql_db.id:
            database = db

    assert str(test_create_sql_db.id) == str(database.id)
    assert str(test_create_sql_db.label) == str(database.label)
    assert database.cluster_size == 1
    assert database.engine == "mysql"
    assert ".g2a.akamaidb.net" in database.hosts.primary


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_update_sql_db(test_linode_client, test_create_sql_db):
    db = test_linode_client.load(MySQLDatabase, test_create_sql_db.id)

    new_allow_list = ["192.168.0.1/32"]
    label = get_test_label() + "updatedSQLDB"

    db.allow_list = new_allow_list
    db.updates.day_of_week = 2
    db.label = label

    res = db.save()

    wait_for_condition(
        30,
        300,
        get_sql_db_status,
        test_linode_client,
        test_create_sql_db.id,
        "active",
    )

    database = test_linode_client.load(MySQLDatabase, test_create_sql_db.id)

    assert res
    assert database.allow_list == new_allow_list
    # assert database.label == label
    assert database.updates.day_of_week == 2


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_get_sql_ssl(test_linode_client, test_create_sql_db):
    db = test_linode_client.load(MySQLDatabase, test_create_sql_db.id)

    assert "ca_certificate" in str(db.ssl)


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_sql_patch(test_linode_client, test_create_sql_db):
    db = test_linode_client.load(MySQLDatabase, test_create_sql_db.id)

    db.patch()

    wait_for_condition(
        10,
        300,
        get_sql_db_status,
        test_linode_client,
        test_create_sql_db.id,
        "updating",
    )

    assert db.status == "updating"

    wait_for_condition(
        30,
        1000,
        get_sql_db_status,
        test_linode_client,
        test_create_sql_db.id,
        "active",
    )

    assert db.status == "active"


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_get_sql_credentials(test_linode_client, test_create_sql_db):
    db = test_linode_client.load(MySQLDatabase, test_create_sql_db.id)

    assert db.credentials.username == "akmadmin"
    assert db.credentials.password


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_reset_sql_credentials(test_linode_client, test_create_sql_db):
    db = test_linode_client.load(MySQLDatabase, test_create_sql_db.id)

    old_pass = str(db.credentials.password)
    db.credentials_reset()

    time.sleep(5)
    assert db.credentials.username == "akmadmin"
    assert db.credentials.password != old_pass


# ------- POSTGRESQL DB Test cases -------
@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_get_postgres_db_instance(test_linode_client, test_create_postgres_db):
    dbs = test_linode_client.database.postgresql_instances()

    database = None

    for db in dbs:
        if db.id == test_create_postgres_db.id:
            database = db

    assert str(test_create_postgres_db.id) == str(database.id)
    assert str(test_create_postgres_db.label) == str(database.label)
    assert database.cluster_size == 1
    assert database.engine == "postgresql"
    assert "g2a.akamaidb.net" in database.hosts.primary


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_update_postgres_db(test_linode_client, test_create_postgres_db):
    db = test_linode_client.load(PostgreSQLDatabase, test_create_postgres_db.id)

    new_allow_list = ["192.168.0.1/32"]
    label = get_test_label() + "updatedPostgresDB"

    db.allow_list = new_allow_list
    db.updates.day_of_week = 2
    db.label = label

    res = db.save()

    wait_for_condition(
        30,
        1000,
        get_postgres_db_status,
        test_linode_client,
        test_create_postgres_db.id,
        "active",
    )

    database = test_linode_client.load(
        PostgreSQLDatabase, test_create_postgres_db.id
    )

    assert res
    assert database.allow_list == new_allow_list
    assert database.label == label
    assert database.updates.day_of_week == 2


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_get_postgres_ssl(test_linode_client, test_create_postgres_db):
    db = test_linode_client.load(PostgreSQLDatabase, test_create_postgres_db.id)

    assert "ca_certificate" in str(db.ssl)


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_postgres_patch(test_linode_client, test_create_postgres_db):
    db = test_linode_client.load(PostgreSQLDatabase, test_create_postgres_db.id)

    db.patch()

    wait_for_condition(
        10,
        300,
        get_postgres_db_status,
        test_linode_client,
        test_create_postgres_db.id,
        "updating",
    )

    assert db.status == "updating"

    wait_for_condition(
        30,
        600,
        get_postgres_db_status,
        test_linode_client,
        test_create_postgres_db.id,
        "active",
    )

    assert db.status == "active"


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_get_postgres_credentials(test_linode_client, test_create_postgres_db):
    db = test_linode_client.load(PostgreSQLDatabase, test_create_postgres_db.id)

    assert db.credentials.username == "akmadmin"
    assert db.credentials.password


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_reset_postgres_credentials(
    test_linode_client, test_create_postgres_db
):
    db = test_linode_client.load(PostgreSQLDatabase, test_create_postgres_db.id)

    old_pass = str(db.credentials.password)

    db.credentials_reset()

    time.sleep(5)

    assert db.credentials.username == "akmadmin"
    assert db.credentials.password != old_pass


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_DB_TESTS environment variable must be set to 'yes' or 'true' (case insensitive)",
)
def test_postgres_suspend_resume(test_linode_client, test_create_postgres_db):
    db = test_linode_client.load(PostgreSQLDatabase, test_create_postgres_db.id)

    db.suspend()

    wait_for_condition(
        10,
        300,
        get_postgres_db_status,
        test_linode_client,
        test_create_postgres_db.id,
        "suspended",
    )

    assert db.status == "suspended"

    db.resume()

    wait_for_condition(
        30,
        600,
        get_postgres_db_status,
        test_linode_client,
        test_create_postgres_db.id,
        "active",
    )

    assert db.status == "active"

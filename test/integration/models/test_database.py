import re
import time
from test.integration.helpers import (
    get_test_label,
    send_request_when_resource_available,
    wait_for_condition,
)

import pytest

from linode_api4 import LinodeClient
from linode_api4.objects import MySQLDatabase, PostgreSQLDatabase


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


@pytest.fixture(scope="session")
def test_create_sql_db(test_linode_client):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
    client = test_linode_client
    label = get_test_label() + "-sqldb"
    region = "us-east"
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
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
    client = test_linode_client
    label = get_test_label() + "-postgresqldb"
    region = "us-east"
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


# ------- SQL DB Test cases -------
def test_get_types(test_linode_client):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
    client = test_linode_client
    types = client.database.types()

    assert (types[0].type_class, "nanode")
    assert (types[0].id, "g6-nanode-1")
    assert (types[0].engines.mongodb[0].price.monthly, 15)


def test_get_engines(test_linode_client):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
    client = test_linode_client
    engines = client.database.engines()

    for e in engines:
        assert e.engine in ["mysql", "postgresql"]
        assert re.search("[0-9]+.[0-9]+", e.version)
        assert e.id == e.engine + "/" + e.version


def test_database_instance(test_linode_client, test_create_sql_db):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
    dbs = test_linode_client.database.mysql_instances()

    assert str(test_create_sql_db.id) in str(dbs.lists)


# ------- POSTGRESQL DB Test cases -------
def test_get_sql_db_instance(test_linode_client, test_create_sql_db):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
    dbs = test_linode_client.database.mysql_instances()
    database = ""
    for db in dbs:
        if db.id == test_create_sql_db.id:
            database = db

    assert str(test_create_sql_db.id) == str(database.id)
    assert str(test_create_sql_db.label) == str(database.label)
    assert database.cluster_size == 1
    assert database.engine == "mysql"
    assert "-mysql-primary.servers.linodedb.net" in database.hosts.primary


def test_update_sql_db(test_linode_client, test_create_sql_db):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
    db = test_linode_client.load(MySQLDatabase, test_create_sql_db.id)

    new_allow_list = ["192.168.0.1/32"]
    label = get_test_label() + "updatedSQLDB"

    db.allow_list = new_allow_list
    db.updates.day_of_week = 2
    db.label = label

    res = db.save()

    database = test_linode_client.load(MySQLDatabase, test_create_sql_db.id)

    wait_for_condition(
        30,
        300,
        get_sql_db_status,
        test_linode_client,
        test_create_sql_db.id,
        "active",
    )

    assert res
    assert database.allow_list == new_allow_list
    assert database.label == label
    assert database.updates.day_of_week == 2


def test_create_sql_backup(test_linode_client, test_create_sql_db):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
    db = test_linode_client.load(MySQLDatabase, test_create_sql_db.id)
    label = "database_backup_test"

    wait_for_condition(
        30,
        300,
        get_sql_db_status,
        test_linode_client,
        test_create_sql_db.id,
        "active",
    )

    db.backup_create(label=label, target="secondary")

    wait_for_condition(
        10,
        300,
        get_sql_db_status,
        test_linode_client,
        test_create_sql_db.id,
        "backing_up",
    )

    assert db.status == "backing_up"

    # list backup and most recently created one is first element of the array
    wait_for_condition(
        30,
        600,
        get_sql_db_status,
        test_linode_client,
        test_create_sql_db.id,
        "active",
    )

    backup = db.backups[0]

    assert backup.label == label
    assert backup.database_id == test_create_sql_db.id

    assert db.status == "active"

    backup.delete()


def test_sql_backup_restore(test_linode_client, test_create_sql_db):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
    db = test_linode_client.load(MySQLDatabase, test_create_sql_db.id)
    try:
        backup = db.backups[0]
    except IndexError as e:
        pytest.skip(
            "Skipping this test. Reason: Couldn't find db backup instance"
        )

    backup.restore()

    wait_for_condition(
        10,
        300,
        get_sql_db_status,
        test_linode_client,
        test_create_sql_db.id,
        "restoring",
    )

    assert db.status == "restoring"

    wait_for_condition(
        30,
        1000,
        get_sql_db_status,
        test_linode_client,
        test_create_sql_db.id,
        "active",
    )

    assert db.status == "active"


def test_get_sql_ssl(test_linode_client, test_create_sql_db):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
    db = test_linode_client.load(MySQLDatabase, test_create_sql_db.id)

    assert "ca_certificate" in str(db.ssl)


def test_sql_patch(test_linode_client, test_create_sql_db):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
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


def test_get_sql_credentials(test_linode_client, test_create_sql_db):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
    db = test_linode_client.load(MySQLDatabase, test_create_sql_db.id)

    assert db.credentials.username == "linroot"
    assert db.credentials.password


def test_reset_sql_credentials(test_linode_client, test_create_sql_db):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
    db = test_linode_client.load(MySQLDatabase, test_create_sql_db.id)

    old_pass = str(db.credentials.password)

    print(old_pass)
    db.credentials_reset()

    time.sleep(5)

    assert db.credentials.username == "linroot"
    assert db.credentials.password != old_pass


# ------- POSTGRESQL DB Test cases -------
def test_get_postgres_db_instance(test_linode_client, test_create_postgres_db):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
    dbs = test_linode_client.database.postgresql_instances()

    for db in dbs:
        if db.id == test_create_postgres_db.id:
            database = db

    assert str(test_create_postgres_db.id) == str(database.id)
    assert str(test_create_postgres_db.label) == str(database.label)
    assert database.cluster_size == 1
    assert database.engine == "postgresql"
    assert "pgsql-primary.servers.linodedb.net" in database.hosts.primary


def test_update_postgres_db(test_linode_client, test_create_postgres_db):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
    db = test_linode_client.load(PostgreSQLDatabase, test_create_postgres_db.id)

    new_allow_list = ["192.168.0.1/32"]
    label = get_test_label() + "updatedPostgresDB"

    db.allow_list = new_allow_list
    db.updates.day_of_week = 2
    db.label = label

    res = db.save()

    database = test_linode_client.load(
        PostgreSQLDatabase, test_create_postgres_db.id
    )

    wait_for_condition(
        30,
        1000,
        get_postgres_db_status,
        test_linode_client,
        test_create_postgres_db.id,
        "active",
    )

    assert res
    assert database.allow_list == new_allow_list
    assert database.label == label
    assert database.updates.day_of_week == 2


def test_create_postgres_backup(test_linode_client, test_create_postgres_db):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
    pytest.skip(
        "Failing due to '400: The backup snapshot request failed, please contact support.'"
    )
    db = test_linode_client.load(PostgreSQLDatabase, test_create_postgres_db.id)
    label = "database_backup_test"

    wait_for_condition(
        30,
        1000,
        get_postgres_db_status,
        test_linode_client,
        test_create_postgres_db.id,
        "active",
    )

    db.backup_create(label=label, target="secondary")

    # list backup and most recently created one is first element of the array
    wait_for_condition(
        10,
        300,
        get_sql_db_status,
        test_linode_client,
        test_create_postgres_db.id,
        "backing_up",
    )

    assert db.status == "backing_up"

    # list backup and most recently created one is first element of the array
    wait_for_condition(
        30,
        600,
        get_sql_db_status,
        test_linode_client,
        test_create_postgres_db.id,
        "active",
    )

    # list backup and most recently created one is first element of the array
    backup = db.backups[0]

    assert backup.label == label
    assert backup.database_id == test_create_postgres_db.id


def test_postgres_backup_restore(test_linode_client, test_create_postgres_db):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
    db = test_linode_client.load(PostgreSQLDatabase, test_create_postgres_db.id)

    try:
        backup = db.backups[0]
    except IndexError as e:
        pytest.skip(
            "Skipping this test. Reason: Couldn't find db backup instance"
        )

    backup.restore()

    wait_for_condition(
        30,
        1000,
        get_postgres_db_status,
        test_linode_client,
        test_create_postgres_db.id,
        "restoring",
    )

    wait_for_condition(
        30,
        1000,
        get_postgres_db_status,
        test_linode_client,
        test_create_postgres_db.id,
        "active",
    )

    assert db.status == "active"


def test_get_postgres_ssl(test_linode_client, test_create_postgres_db):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
    db = test_linode_client.load(PostgreSQLDatabase, test_create_postgres_db.id)

    assert "ca_certificate" in str(db.ssl)


def test_postgres_patch(test_linode_client, test_create_postgres_db):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
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


def test_get_postgres_credentials(test_linode_client, test_create_postgres_db):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
    db = test_linode_client.load(PostgreSQLDatabase, test_create_postgres_db.id)

    assert db.credentials.username == "linpostgres"
    assert db.credentials.password


def test_reset_postgres_credentials(
    test_linode_client, test_create_postgres_db
):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )
    db = test_linode_client.load(PostgreSQLDatabase, test_create_postgres_db.id)

    old_pass = str(db.credentials.password)

    db.credentials_reset()

    time.sleep(5)

    assert db.credentials.username == "linpostgres"
    assert db.credentials.password != old_pass

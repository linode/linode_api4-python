import re
import pytest
import os

from linode_api4 import LinodeClient
from linode_api4.objects import (
    Account,
    AccountSettings,
    Database,
    Domain,
    Event,
    Firewall,
    Image,
    Instance,
    Invoice,
    Login,
    LongviewClient,
    NodeBalancer,
    OAuthClient,
    PaymentMethod,
    ServiceTransfer,
    StackScript,
    User,
    Volume,
    get_obj_grants,
)
from test.integration.helpers import get_test_label, wait_for_condition
from linode_api4.objects import MySQLDatabase
from typing import Any


# Test Helpers
def get_db_engine_id(client: LinodeClient, engine: str):
    engines = client.database.engines()
    engine_id = ""
    for e in engines:
        if e.engine == engine:
            engine_id = e.id

    return str(engine_id)


@pytest.fixture(scope="session")
def test_create_sql_db(get_client):
    client = get_client
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
        print(db.status)
        return db.status == "active"

    # TAKES 15-30 MINUTES TO FULLY PROVISION DB
    wait_for_condition(60, 2000, get_db_status)

    yield db

    db.delete()


# @pytest.mark.skipif(
#     os.environ.get("RUN_LONG_TESTS", None) != True,
#     reason="Skipping long-running Test, to run set RUN_LONG_TESTS=TRUE",
# )
# @pytest.fixture(scope="session")
# def test_create_postgres_db(get_client):
#     client = get_client
#     label = get_test_label() + "-postgresqldb"
#     region = "us-east"
#     engine_id = get_db_engine_id(client, "postgresql")
#     dbtype = "g6-standard-1"
#
#     db = client.database.postgresql_create(
#         label=label,
#         region=region,
#         engine=engine_id,
#         ltype=dbtype,
#         cluster_size=None,
#     )
#
#     def get_db_status():
#         return db.status == "active"
#
#     # TAKES 15-30 MINUTES TO FULLY PROVISION DB
#     wait_for_condition(60, 1800, get_db_status)
#
#     yield db
#
#     db.delete()
#
#
# @pytest.mark.skipif(
#     os.environ.get("RUN_LONG_TESTS", None) != True,
#     reason="Skipping long-running Test, to run set RUN_LONG_TESTS=TRUE",
# )
# @pytest.fixture(scope="session")
# def test_create_mongo_db(get_client):
#     client = get_client
#     label = get_test_label() + "-mongo"
#     region = "us-east"
#     engine_id = get_db_engine_id(client, "mongodb")
#     dbtype = "g6-standard-1"
#
#     if engine_id:
#         db = client.database.mongodb_create(
#             label=label,
#             region=region,
#             engine=engine_id,
#             ltype=dbtype,
#             cluster_size=None,
#         )
#     else:
#         pytest.skip("MongoDB is not one of available options")
#
#     def get_db_status():
#         return db.status == "active"
#
#     # TAKES 15-30 MINUTES TO FULLY PROVISION DB
#     wait_for_condition(60, 1800, get_db_status)
#
#     yield db
#
#     db.delete()


def test_get_types(get_client):
    client = get_client
    types = client.database.types()

    assert(types[0].type_class, "nanode")
    assert(types[0].id, "g6-nanode-1")
    assert(types[0].engines.mongodb[0].price.monthly, 15)


def test_get_engines(get_client):
    client = get_client
    engines = client.database.engines()

    for e in engines:
        assert e.engine in ['mysql', 'postgresql']
        assert re.search("[0-9]+.[0-9]+", e.version)
        assert e.id == e.engine + "/" + e.version


def test_database_instances(get_client, test_create_sql_db):
    dbs = get_client.database.mysql_instances()

    assert str(test_create_sql_db.id) in str(dbs.lists)
    # assert str(test_create_postgres_db.id) in str(dbs.lists)


def test_get_sql_db_instance(get_client, test_create_sql_db):
    dbs = get_client.database.mysql_instances()
    database = ""
    for db in dbs:
        if db.id == test_create_sql_db.id:
            database = db

    assert str(test_create_sql_db.id) == str(database.id)
    assert str(test_create_sql_db.label) == str(database.label)
    assert database.cluster_size == 1
    assert database.engine == "mysql"
    assert "-mysql-primary.servers.linodedb.net" in database.hosts.primary


def test_update_sql_db(get_client, test_create_sql_db):
    db = get_client.load(MySQLDatabase, test_create_sql_db.id)

    new_allow_list = ["192.168.0.1/32"]
    label = get_test_label() + "updatedSQLDB"

    db.allow_list = new_allow_list
    db.updates.day_of_week = 2
    db.label = label

    res = db.save()

    database = get_client.load(MySQLDatabase, test_create_sql_db.id)

    def get_db_status():
        return database.status == "active"

    wait_for_condition(interval=30, timeout=300, condition=get_db_status())

    assert res
    assert database.allow_list == new_allow_list
    assert database.label == label
    assert database.updates.day_of_week == 2


def test_create_sql_backup(get_client, test_create_sql_db):
    db = get_client.load(MySQLDatabase, test_create_sql_db.id)
    label = get_test_label() + "-backup"
    db.backup_create(label=label, target="secondary")

    def get_db_status():
        return db.status == "active"

    # Wait
    wait_for_condition(interval=30, timeout=300, condition=get_db_status())

    # list backup and most recently created one is first element of the array
    backup = db.backups[0]

    assert backup.label == label
    assert backup.database_id == test_create_sql_db.id


def test_sql_backup_restore(get_client, test_create_sql_db):
    db = get_client.load(MySQLDatabase, test_create_sql_db.id)
    backup = db.backups[0]

    def get_db_status(status: str):
        return db.status == status

    if backup:
        backup.restore()
        wait_for_condition(interval=30, timeout=300, condition=get_db_status(status="restoring"))
    else:
        pytest.skip("Skipping this test. Reason: Couldn't find db backup instance")

    wait_for_condition(interval=30, timeout=300, condition=get_db_status(status="active"))

    assert db.status == "active"

#@pytest.mark.skipif(
#     os.environ.get("RUN_LONG_TESTS", None) != True,
#     reason="Skipping long-running Test, to run set RUN_LONG_TESTS=TRUE",
# )
# def test_get_sql_ssl(get_client, test_create_sql_db):
#     db = get_client.load(MySQLDatabase, test_create_sql_db.id)
#
#     assert "ca_certificate" in str(db.ssl)
#
#
#@pytest.mark.skipif(
#     os.environ.get("RUN_LONG_TESTS", None) != True,
#     reason="Skipping long-running Test, to run set RUN_LONG_TESTS=TRUE",
# )
# def test_sql_patch(get_client,test_create_sql_db):
#     db = get_client.load(MySQLDatabase, test_create_sql_db.id)
#
#     db.patch()
#
#     wait_for_condition(interval=30, timeout=300, condition=get_db_status(database=db, status="active"))
#
#     assert db.status == "active"
#
##@pytest.mark.skipif(
#     os.environ.get("RUN_LONG_TESTS", None) != True,
#     reason="Skipping long-running Test, to run set RUN_LONG_TESTS=TRUE",
# )
# def test_get_sql_credentials(get_client, test_create_sql_db):
#     db = get_client.load(MySQLDatabase, test_create_sql_db.id)
#
#     assert db.credentials.username == 'linroot'
#     assert db.credentials.password # Note asserting if the password just exists since it is randomly generated one
#
#
#@pytest.mark.skipif(
#     os.environ.get("RUN_LONG_TESTS", None) != True,
#     reason="Skipping long-running Test, to run set RUN_LONG_TESTS=TRUE",
# )
# def test_reset_sql_credentials(get_client, test_create_sql_db):
#     db = get_client.load(MySQLDatabase, test_create_sql_db.id)
#
#     old_pass = db.credentials.password
#
#     db.credentials_reset()
#
#     assert db.credentials.username == 'linroot'
#     assert db.credentials.password != old_pass# Note asserting if the password just exists since it is randomly generated one

# def test_get_postgres_db_instance():
#
#
# def test_create_postgres_db():
#
#
# def test_update_postgres_db():
#
#
# def test_list_postgres_backups():
#
#
# def test_create_postgres_backup():
#
#
# def test_postgres_backup_restore():
#
#
# def test_postgres_patch():
#
#
# def test_get_postgres_ssl():
#
#
# def test_get_postgres_credentials():
#
#
# def test_reset_postgres_credentials():
#
#
# def test_get_mongo_db_instance():
#
# def test_create_mongo_db():
#
#
# def test_update_mongo_db():
#
#
# def test_list_mongo_backups():
#
#
# def test_create_mongo_backup():
#
#
# def test_mongo_backup_restore():
#
#
# def test_mongo_patch():
#
#
# def test_get_mongo_ssl():
#
#
# def test_get_mongo_credentials():
#
#
# def test_reset_mongo_credentials():




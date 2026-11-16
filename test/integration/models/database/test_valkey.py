import os
from dataclasses import fields
from test.integration.conftest import get_region
from test.integration.helpers import (
    get_test_label,
    send_request_when_resource_available,
    wait_for_condition,
)

import pytest

from linode_api4 import (
    Capability,
    DatabaseEngine,
    DatabasePrivateNetwork,
    ExplicitNullValue,
    ValkeyDatabase,
    ValkeyDatabaseConfigOptions,
)

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_VALKEY_DB_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="RUN_VALKEY_DB_TESTS must be 'yes' or 'true'; creates real databases",
)


def wait_for_valkey_status(client, database, status):
    wait_for_condition(
        30,
        1200,
        lambda: client.load(ValkeyDatabase, database.id).status == status,
    )
    database.invalidate()


@pytest.fixture
def create_valkey_database(test_linode_client, request):
    client = test_linode_client
    engines = list(client.database.engines(DatabaseEngine.engine == "valkey"))
    assert engines, "No Valkey database engine is available to this account"
    types = [
        node_type
        for node_type in client.database.types()
        if not node_type.deprecated and getattr(node_type.engines, "valkey", [])
    ]
    assert types, "No Valkey-capable database type is available to this account"
    node_type = min(types, key=lambda candidate: candidate.memory)

    def create(**kwargs):
        params = {
            "label": get_test_label() + "-valkey",
            "region": os.getenv("LINODE_TEST_REGION_OVERRIDE", "us-ord"),
            "engine": engines[0].id,
            "ltype": node_type.id,
            "cluster_size": 1,
            "engine_config": ValkeyDatabaseConfigOptions(
                valkey_persistence="rdb",
                frequent_snapshots=True,
                valkey_timeout=300,
            ),
        }
        params.update(kwargs)
        database = client.database.valkey_create(**params)
        request.addfinalizer(
            lambda: send_request_when_resource_available(600, database.delete)
        )
        wait_for_valkey_status(client, database, "active")
        return database

    return create


def test_valkey_config_catalog(test_linode_client):
    catalog = test_linode_client.database.valkey_config_options()
    assert {field.name for field in fields(ValkeyDatabaseConfigOptions)} <= set(
        catalog
    )
    assert catalog["backup_hour"]["type"] == ["integer", "null"]
    assert catalog["backup_minute"]["type"] == ["integer", "null"]
    assert catalog["valkey_acl_channels_default"]["enum"] == [
        "allchannels",
        "resetchannels",
    ]
    assert catalog["valkey_number_of_databases"]["requires_restart"]


def test_valkey_lifecycle(test_linode_client, create_valkey_database):
    client = test_linode_client
    database = create_valkey_database()
    assert database.engine == "valkey"
    assert database.engine_config.valkey_persistence == "rdb"
    assert any(
        db.id == database.id for db in client.database.valkey_instances()
    )
    generic = next(
        db for db in client.database.instances() if db.id == database.id
    )
    assert isinstance(generic.instance, ValkeyDatabase)
    assert generic.instance.id == database.id
    assert database.ssl.ca_certificate
    assert database.credentials.username
    password = database.credentials.password
    assert password

    database.engine_config = ValkeyDatabaseConfigOptions(valkey_timeout=301)
    database.allow_list = ["192.0.2.0/24"]
    assert send_request_when_resource_available(300, database.save)

    def updated():
        db = client.load(ValkeyDatabase, database.id)
        return (
            db.status == "active"
            and db.engine_config.valkey_timeout == 301
            and db.allow_list == ["192.0.2.0/24"]
        )

    wait_for_condition(30, 1200, updated)
    send_request_when_resource_available(300, database.credentials_reset)

    def password_changed():
        database.invalidate()
        return database.credentials.password != password

    wait_for_condition(10, 300, password_changed)
    send_request_when_resource_available(300, database.patch)
    wait_for_valkey_status(client, database, "active")
    send_request_when_resource_available(300, database.suspend)
    wait_for_valkey_status(client, database, "suspended")
    database.resume()
    wait_for_valkey_status(client, database, "active")


@pytest.mark.skipif(
    os.getenv("RUN_VALKEY_DB_FORK_TESTS", "").strip().lower()
    not in {"yes", "true"},
    reason="RUN_VALKEY_DB_FORK_TESTS must be 'yes' or 'true'; creates forked databases",
)
@pytest.mark.parametrize("latest", [False, True])
def test_valkey_fork(
    test_linode_client, create_valkey_database, request, latest
):
    client = test_linode_client
    source = create_valkey_database()
    snapshots = wait_for_condition(
        30,
        1800,
        lambda: client.load(ValkeyDatabase, source.id).available_restore_times,
    )
    fork = client.database.valkey_fork(
        source.id,
        None if latest else snapshots[-1],
        label=get_test_label() + "-valkey-fork",
    )
    request.addfinalizer(
        lambda: send_request_when_resource_available(600, fork.delete)
    )
    wait_for_valkey_status(client, fork, "active")
    assert fork.fork.source == source.id
    if not latest:
        assert fork.fork.restore_time == snapshots[-1]


def test_valkey_private_network(
    test_linode_client, create_valkey_database, request
):
    client = test_linode_client
    region = get_region(client, {Capability.vpcs, Capability.linodes})
    vpc = client.vpcs.create(
        label=get_test_label(),
        region=region,
        description="Valkey private-network integration test",
    )
    request.addfinalizer(
        lambda: send_request_when_resource_available(600, vpc.delete)
    )
    subnet = vpc.subnet_create(
        label=get_test_label(),
        ipv4="10.0.0.0/24",
    )
    request.addfinalizer(
        lambda: send_request_when_resource_available(600, subnet.delete)
    )
    database = create_valkey_database(
        region=region,
        private_network=DatabasePrivateNetwork(
            vpc_id=vpc.id, subnet_id=subnet.id, public_access=False
        ),
    )
    assert database.private_network.vpc_id == vpc.id
    assert database.private_network.subnet_id == subnet.id
    assert database.private_network.public_access is False
    database.private_network = ExplicitNullValue()
    assert send_request_when_resource_available(300, database.save)
    wait_for_condition(
        30,
        1200,
        lambda: client.load(ValkeyDatabase, database.id).private_network
        is None,
    )

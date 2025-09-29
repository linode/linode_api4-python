import ipaddress
import os
import random
import time
from test.integration.helpers import (
    get_test_label,
    send_request_when_resource_available,
    wait_for_condition,
)
from test.integration.models.database.helpers import get_db_engine_id
from typing import Optional, Set

import pytest
import requests
from requests.exceptions import ConnectionError, RequestException

from linode_api4 import (
    ExplicitNullValue,
    InterfaceGeneration,
    LinodeInterfaceDefaultRouteOptions,
    LinodeInterfaceOptions,
    LinodeInterfacePublicOptions,
    LinodeInterfaceVLANOptions,
    LinodeInterfaceVPCOptions,
    PlacementGroupPolicy,
    PlacementGroupType,
    PostgreSQLDatabase,
)
from linode_api4.linode_client import LinodeClient, MonitorClient
from linode_api4.objects import Region

ENV_TOKEN_NAME = "LINODE_TOKEN"
ENV_API_URL_NAME = "LINODE_API_URL"
ENV_REGION_OVERRIDE = "LINODE_TEST_REGION_OVERRIDE"
ENV_API_CA_NAME = "LINODE_API_CA"
RUN_LONG_TESTS = "RUN_LONG_TESTS"


def get_token():
    return os.environ.get(ENV_TOKEN_NAME, None)


def get_api_url():
    return os.environ.get(ENV_API_URL_NAME, "https://api.linode.com/v4beta")


def get_regions(
    client: LinodeClient,
    capabilities: Optional[Set[str]] = None,
    site_type: Optional[str] = None,
):
    region_override = os.environ.get(ENV_REGION_OVERRIDE)

    # Allow overriding the target test region
    if region_override is not None:
        return Region(client, region_override)

    regions = client.regions()

    if capabilities is not None:
        regions = [
            v for v in regions if set(capabilities).issubset(v.capabilities)
        ]

    if site_type is not None:
        regions = [v for v in regions if v.site_type == site_type]

    return regions


def get_region(
    client: LinodeClient, capabilities: Set[str] = None, site_type: str = "core"
):
    return random.choice(get_regions(client, capabilities, site_type))


def get_api_ca_file():
    result = os.environ.get(ENV_API_CA_NAME, None)
    return result if result != "" else None


def run_long_tests():
    return os.environ.get(RUN_LONG_TESTS, None)


@pytest.fixture(autouse=True, scope="session")
def e2e_test_firewall(test_linode_client):
    def is_valid_ipv4(address):
        try:
            ipaddress.IPv4Address(address)
            return True
        except ipaddress.AddressValueError:
            return False

    def is_valid_ipv6(address):
        try:
            ipaddress.IPv6Address(address)
            return True
        except ipaddress.AddressValueError:
            return False

    def get_public_ip(ip_version: str = "ipv4", retries: int = 3):
        url = (
            f"https://api64.ipify.org?format=json"
            if ip_version == "ipv6"
            else f"https://api.ipify.org?format=json"
        )
        for attempt in range(retries):
            try:
                response = requests.get(url)
                response.raise_for_status()
                return str(response.json()["ip"])
            except (RequestException, ConnectionError) as e:
                if attempt < retries - 1:
                    time.sleep(2)  # Wait before retrying
                else:
                    raise e

    def create_inbound_rule(ipv4_address, ipv6_address):
        rule = [
            {
                "protocol": "TCP",
                "ports": "22",
                "addresses": {},
                "action": "ACCEPT",
            }
        ]
        if is_valid_ipv4(ipv4_address):
            rule[0]["addresses"]["ipv4"] = [f"{ipv4_address}/32"]

        if is_valid_ipv6(ipv6_address):
            rule[0]["addresses"]["ipv6"] = [f"{ipv6_address}/128"]

        return rule

    try:
        ipv4_address = get_public_ip("ipv4")
    except (RequestException, ConnectionError, ValueError, KeyError):
        ipv4_address = None

    try:
        ipv6_address = get_public_ip("ipv6")
    except (RequestException, ConnectionError, ValueError, KeyError):
        ipv6_address = None

    inbound_rule = []
    if ipv4_address or ipv6_address:
        inbound_rule = create_inbound_rule(ipv4_address, ipv6_address)

    client = test_linode_client

    rules = {
        "outbound": [],
        "outbound_policy": "ACCEPT",
        "inbound": inbound_rule,
        "inbound_policy": "DROP",
    }

    label = "cloud_firewall_" + str(int(time.time()))

    firewall = client.networking.firewall_create(
        label=label, rules=rules, status="enabled"
    )

    yield firewall

    firewall.delete()


@pytest.fixture(scope="session")
def create_linode(test_linode_client, e2e_test_firewall):
    client = test_linode_client

    region = get_region(client, {"Linodes", "Cloud Firewall"}, site_type="core")
    label = get_test_label(length=8)

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1",
        region,
        image="linode/debian12",
        label=label,
        firewall=e2e_test_firewall,
    )

    yield linode_instance

    linode_instance.delete()


@pytest.fixture
def create_linode_for_pass_reset(test_linode_client, e2e_test_firewall):
    client = test_linode_client

    region = get_region(client, {"Linodes", "Cloud Firewall"}, site_type="core")
    label = get_test_label(length=8)

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1",
        region,
        image="linode/debian12",
        label=label,
        firewall=e2e_test_firewall,
    )

    yield linode_instance, password

    linode_instance.delete()


@pytest.fixture(scope="session")
def ssh_key_gen():
    output = os.popen("ssh-keygen -q -t rsa -f ./sdk-sshkey  -q -N ''")

    time.sleep(1)

    pub_file = open("./sdk-sshkey.pub", "r")
    pub_key = pub_file.read().rstrip()

    priv_file = open("./sdk-sshkey", "r")
    priv_key = priv_file.read().rstrip()

    yield pub_key, priv_key

    os.popen("rm ./sdk-sshkey*")


@pytest.fixture(scope="session")
def test_linode_client():
    token = get_token()
    api_url = get_api_url()
    api_ca_file = get_api_ca_file()
    client = LinodeClient(
        token,
        base_url=api_url,
        ca_path=api_ca_file,
    )
    return client


@pytest.fixture
def test_account_settings(test_linode_client):
    client = test_linode_client
    account_settings = client.account.settings()
    account_settings._populated = True
    account_settings.network_helper = True

    account_settings.save()


@pytest.fixture(scope="session")
def test_domain(test_linode_client):
    client = test_linode_client

    timestamp = str(time.time_ns())
    domain_addr = timestamp + "-example.com"
    soa_email = "pathiel-test123@linode.com"

    domain = client.domain_create(
        domain=domain_addr, soa_email=soa_email, tags=["test-tag"]
    )

    # Create a SRV record
    domain.record_create(
        "SRV",
        target="rc_test",
        priority=10,
        weight=5,
        port=80,
        service="service_test",
    )

    yield domain

    domain.delete()


@pytest.fixture(scope="session")
def test_volume(test_linode_client):
    client = test_linode_client
    region = get_region(client, {"Linodes", "Cloud Firewall"}, site_type="core")
    label = get_test_label(length=8)

    volume = client.volume_create(label=label, region=region)

    yield volume

    send_request_when_resource_available(timeout=100, func=volume.delete)


@pytest.fixture(scope="session")
def test_volume_with_encryption(test_linode_client):
    client = test_linode_client
    region = get_region(client, {"Block Storage Encryption"})
    label = get_test_label(length=8)

    volume = client.volume_create(
        label=label, region=region, encryption="enabled"
    )

    yield volume

    send_request_when_resource_available(timeout=100, func=volume.delete)


@pytest.fixture
def test_tag(test_linode_client):
    client = test_linode_client

    label = get_test_label(length=8)

    tag = client.tag_create(label=label)

    yield tag

    tag.delete()


@pytest.fixture
def test_nodebalancer(test_linode_client):
    client = test_linode_client

    label = get_test_label(length=8)

    nodebalancer = client.nodebalancer_create(
        region=get_region(client, capabilities={"NodeBalancers"}), label=label
    )

    yield nodebalancer

    nodebalancer.delete()


@pytest.fixture
def test_longview_client(test_linode_client):
    client = test_linode_client
    label = get_test_label(length=8)
    longview_client = client.longview.client_create(label=label)

    yield longview_client

    longview_client.delete()


@pytest.fixture
def test_sshkey(test_linode_client, ssh_key_gen):
    pub_key = ssh_key_gen[0]
    client = test_linode_client
    key_label = get_test_label(8) + "_key"
    key = client.profile.ssh_key_upload(pub_key, key_label)

    yield key

    key.delete()


@pytest.fixture
def access_keys_object_storage(test_linode_client):
    client = test_linode_client
    label = get_test_label(length=8)
    key = client.object_storage.keys_create(label)

    yield key

    key.delete()


@pytest.fixture(scope="session")
def test_firewall(test_linode_client):
    client = test_linode_client
    rules = {
        "outbound": [],
        "outbound_policy": "DROP",
        "inbound": [],
        "inbound_policy": "ACCEPT",
    }

    label = get_test_label(8) + "_firewall"

    firewall = client.networking.firewall_create(
        label=label, rules=rules, status="enabled"
    )

    yield firewall

    firewall.delete()


@pytest.fixture
def test_oauth_client(test_linode_client):
    client = test_linode_client
    label = get_test_label(length=8) + "_oauth"

    oauth_client = client.account.oauth_client_create(
        label, "https://localhost/oauth/callback"
    )

    yield oauth_client

    oauth_client.delete()


@pytest.fixture(scope="session")
def create_vpc(test_linode_client):
    client = test_linode_client

    label = get_test_label(length=10)

    vpc = client.vpcs.create(
        label,
        get_region(test_linode_client, {"VPCs"}),
        description="test description",
    )
    yield vpc

    vpc.delete()


@pytest.fixture(scope="session")
def create_vpc_with_subnet(test_linode_client, create_vpc):
    subnet = create_vpc.subnet_create("test-subnet", ipv4="10.0.0.0/24")

    yield create_vpc, subnet

    subnet.delete()


@pytest.fixture(scope="session")
def create_vpc_with_subnet_and_linode(
    test_linode_client, create_vpc_with_subnet, e2e_test_firewall
):
    vpc, subnet = create_vpc_with_subnet

    label = get_test_label(length=8)

    instance, password = test_linode_client.linode.instance_create(
        "g6-standard-1",
        vpc.region,
        image="linode/debian11",
        label=label,
        firewall=e2e_test_firewall,
    )

    yield vpc, subnet, instance, password

    instance.delete()


@pytest.fixture(scope="session")
def create_multiple_vpcs(test_linode_client):
    client = test_linode_client

    label = get_test_label(length=10)

    label_2 = get_test_label(length=10)

    vpc_1 = client.vpcs.create(
        label,
        get_region(test_linode_client, {"VPCs"}),
        description="test description",
    )

    vpc_2 = client.vpcs.create(
        label_2,
        get_region(test_linode_client, {"VPCs"}),
        description="test description",
    )

    yield vpc_1, vpc_2

    vpc_1.delete()

    vpc_2.delete()


@pytest.fixture(scope="session")
def create_placement_group(test_linode_client):
    client = test_linode_client

    label = get_test_label(10)

    pg = client.placement.group_create(
        label,
        get_region(test_linode_client, {"Placement Group"}),
        PlacementGroupType.anti_affinity_local,
        PlacementGroupPolicy.flexible,
    )
    yield pg

    pg.delete()


@pytest.fixture(scope="session")
def create_placement_group_with_linode(
    test_linode_client, create_placement_group
):
    client = test_linode_client

    inst = client.linode.instance_create(
        "g6-nanode-1",
        create_placement_group.region,
        label=create_placement_group.label,
        placement_group=create_placement_group,
    )

    create_placement_group.invalidate()

    yield create_placement_group, inst

    inst.delete()


@pytest.mark.smoke
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "smoke: mark test as part of smoke test suite",
    )


@pytest.fixture(scope="session")
def linode_for_vlan_tests(test_linode_client, e2e_test_firewall):
    client = test_linode_client
    region = get_region(client, {"Linodes", "Vlans"}, site_type="core")
    label = get_test_label(length=8)

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1",
        region,
        image="linode/debian12",
        label=label,
        firewall=e2e_test_firewall,
    )

    yield linode_instance

    linode_instance.delete()


@pytest.fixture(scope="function")
def linode_with_interface_generation_linode(
    test_linode_client,
    e2e_test_firewall,
    # We won't be using this all the time, but it's
    # necessary for certain consumers of this fixture
    create_vpc_with_subnet,
):
    client = test_linode_client

    label = get_test_label()

    instance = client.linode.instance_create(
        "g6-nanode-1",
        create_vpc_with_subnet[0].region,
        label=label,
        interface_generation=InterfaceGeneration.LINODE,
        booted=False,
    )

    yield instance

    instance.delete()


@pytest.fixture(scope="function")
def linode_with_linode_interfaces(
    test_linode_client, e2e_test_firewall, create_vpc_with_subnet
):
    client = test_linode_client
    vpc, subnet = create_vpc_with_subnet

    # Are there regions where VPCs are supported but Linode Interfaces aren't?
    region = vpc.region
    label = get_test_label()

    instance, _ = client.linode.instance_create(
        "g6-nanode-1",
        region,
        image="linode/debian12",
        label=label,
        booted=False,
        interface_generation=InterfaceGeneration.LINODE,
        interfaces=[
            LinodeInterfaceOptions(
                firewall_id=e2e_test_firewall.id,
                default_route=LinodeInterfaceDefaultRouteOptions(
                    ipv4=True,
                    ipv6=True,
                ),
                public=LinodeInterfacePublicOptions(),
            ),
            LinodeInterfaceOptions(
                firewall_id=ExplicitNullValue,
                vpc=LinodeInterfaceVPCOptions(
                    subnet_id=subnet.id,
                ),
            ),
            LinodeInterfaceOptions(
                vlan=LinodeInterfaceVLANOptions(
                    vlan_label="test-vlan", ipam_address="10.0.0.5/32"
                ),
            ),
        ],
    )

    yield instance

    instance.delete()


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


@pytest.fixture(scope="session")
def get_monitor_token_for_db_entities(
    test_linode_client, test_create_postgres_db
):
    client = test_linode_client

    dbs = client.database.postgresql_instances()

    if len(dbs) < 1:
        db_id = test_create_postgres_db.id
    else:
        db_id = dbs[0].id

    region = client.load(PostgreSQLDatabase, db_id).region
    dbs = client.database.instances()

    # only collect entity_ids in the same region
    entity_ids = [db.id for db in dbs if db.region == region]

    # create token for the particular service
    token = client.monitor.create_token(
        service_type="dbaas", entity_ids=entity_ids
    )

    yield token, entity_ids


@pytest.fixture(scope="session")
def test_monitor_client(get_monitor_token_for_db_entities):
    api_ca_file = get_api_ca_file()
    token, entity_ids = get_monitor_token_for_db_entities

    client = MonitorClient(
        token.token,
        ca_path=api_ca_file,
    )

    return client, entity_ids

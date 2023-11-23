import os
import random
import time
from typing import Set

import pytest

from linode_api4 import ApiError
from linode_api4.linode_client import LinodeClient
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


def get_region(client: LinodeClient, capabilities: Set[str] = None):
    region_override = os.environ.get(ENV_REGION_OVERRIDE)

    # Allow overriding the target test region
    if region_override is not None:
        return Region(client, region_override)

    regions = client.regions()

    if capabilities is not None:
        regions = [
            v for v in regions if set(capabilities).issubset(v.capabilities)
        ]

    return random.choice(regions)


def get_api_ca_file():
    result = os.environ.get(ENV_API_CA_NAME, None)
    return result if result != "" else None


def run_long_tests():
    return os.environ.get(RUN_LONG_TESTS, None)


@pytest.fixture(scope="session")
def create_linode(test_linode_client):
    client = test_linode_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    timestamp = str(time.time_ns())
    label = "TestSDK-" + timestamp

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1", chosen_region, image="linode/debian10", label=label
    )

    yield linode_instance

    linode_instance.delete()


@pytest.fixture
def create_linode_for_pass_reset(test_linode_client):
    client = test_linode_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    timestamp = str(time.time_ns())
    label = "TestSDK-" + timestamp

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1", chosen_region, image="linode/debian10", label=label
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
    timestamp = str(time.time_ns())
    region = client.regions()[0]
    label = "TestSDK-" + timestamp

    volume = client.volume_create(label=label, region=region)

    yield volume

    timeout = 100  # give 100s for volume to be detached before deletion

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            res = volume.delete()
            if res:
                break
            else:
                time.sleep(3)
        except ApiError as e:
            if time.time() - start_time > timeout:
                raise e


@pytest.fixture
def test_tag(test_linode_client):
    client = test_linode_client

    timestamp = str(time.time_ns())
    label = "TestSDK-" + timestamp

    tag = client.tag_create(label=label)

    yield tag

    tag.delete()


@pytest.fixture
def test_nodebalancer(test_linode_client):
    client = test_linode_client

    timestamp = str(time.time_ns())
    label = "TestSDK-" + timestamp

    nodebalancer = client.nodebalancer_create(
        region=get_region(client), label=label
    )

    yield nodebalancer

    nodebalancer.delete()


@pytest.fixture
def test_longview_client(test_linode_client):
    client = test_linode_client
    timestamp = str(time.time_ns())
    label = "TestSDK-" + timestamp
    longview_client = client.longview.client_create(label=label)

    yield longview_client

    longview_client.delete()


@pytest.fixture
def test_sshkey(test_linode_client, ssh_key_gen):
    pub_key = ssh_key_gen[0]
    client = test_linode_client
    key = client.profile.ssh_key_upload(pub_key, "IntTestSDK-sshkey")

    yield key

    key.delete()


@pytest.fixture
def ssh_keys_object_storage(test_linode_client):
    client = test_linode_client
    label = "TestSDK-obj-storage-key"
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

    firewall = client.networking.firewall_create(
        "test-firewall", rules=rules, status="enabled"
    )

    yield firewall

    firewall.delete()


@pytest.fixture
def test_oauth_client(test_linode_client):
    client = test_linode_client
    oauth_client = client.account.oauth_client_create(
        "test-oauth-client", "https://localhost/oauth/callback"
    )

    yield oauth_client

    oauth_client.delete()


@pytest.fixture(scope="session")
def create_vpc(test_linode_client):
    client = test_linode_client

    timestamp = str(int(time.time()))

    vpc = client.vpcs.create(
        "pythonsdk-" + timestamp,
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
    test_linode_client, create_vpc_with_subnet
):
    vpc, subnet = create_vpc_with_subnet

    timestamp = str(int(time.time()))
    label = "TestSDK-" + timestamp

    instance, password = test_linode_client.linode.instance_create(
        "g5-standard-4", vpc.region, image="linode/debian11", label=label
    )

    yield vpc, subnet, instance, password

    instance.delete()


@pytest.fixture(scope="session")
def create_vpc(test_linode_client):
    client = test_linode_client

    timestamp = str(int(time.time_ns() % 10**10))

    vpc = client.vpcs.create(
        "pythonsdk-" + timestamp,
        get_region(test_linode_client, {"VPCs"}),
        description="test description",
    )
    yield vpc

    vpc.delete()


@pytest.fixture(scope="session")
def create_multiple_vpcs(test_linode_client):
    client = test_linode_client

    timestamp = str(int(time.time_ns() % 10**10))

    timestamp_2 = str(int(time.time_ns() % 10**10))

    vpc_1 = client.vpcs.create(
        "pythonsdk-" + timestamp,
        get_region(test_linode_client, {"VPCs"}),
        description="test description",
    )

    vpc_2 = client.vpcs.create(
        "pythonsdk-" + timestamp_2,
        get_region(test_linode_client, {"VPCs"}),
        description="test description",
    )

    yield vpc_1, vpc_2

    vpc_1.delete()

    vpc_2.delete()

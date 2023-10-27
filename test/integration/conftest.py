import os
import time

import pytest

from linode_api4.linode_client import LinodeClient

from linode_api4 import ApiError


ENV_TOKEN_NAME = "LINODE_TOKEN"
ENV_API_URL_NAME = "LINODE_API_URL"
ENV_API_CA_NAME = "LINODE_API_CA"
RUN_LONG_TESTS = "RUN_LONG_TESTS"


def get_token():
    return os.environ.get(ENV_TOKEN_NAME, None)


def get_api_url():
    return os.environ.get(ENV_API_URL_NAME, "https://api.linode.com/v4beta")


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
    timestamp = str(int(time.time_ns()))
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
    timestamp = str(int(time.time_ns()))
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

    timestamp = str(int(time.time_ns()))
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
    timestamp = str(int(time.time_ns()))
    label = "TestSDK-" + timestamp

    volume = client.volume_create(label=label, region="ap-west")

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

    timestamp = str(int(time.time_ns()))
    label = "TestSDK-" + timestamp

    tag = client.tag_create(label=label)

    yield tag

    tag.delete()


@pytest.fixture
def test_nodebalancer(test_linode_client):
    client = test_linode_client

    timestamp = str(int(time.time_ns()))
    label = "TestSDK-" + timestamp

    nodebalancer = client.nodebalancer_create(region="us-east", label=label)

    yield nodebalancer

    nodebalancer.delete()


@pytest.fixture
def test_longview_client(test_linode_client):
    client = test_linode_client
    timestamp = str(int(time.time_ns()))
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

import os
import time

import pytest

from linode_api4.linode_client import LinodeClient, LongviewSubscription

ENV_TOKEN_NAME = "LINODE_TOKEN"
RUN_LONG_TESTS = "RUN_LONG_TESTS"


def get_token():
    return os.environ.get(ENV_TOKEN_NAME, None)


def run_long_tests():
    return os.environ.get(RUN_LONG_TESTS, None)


@pytest.fixture(scope="session")
def create_linode(get_client):
    client = get_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    timestamp = str(int(time.time()))
    label = "TestSDK-" + timestamp

    linode_instance, password = client.linode.instance_create(
        "g5-standard-4", chosen_region, image="linode/debian9", label=label
    )

    yield linode_instance

    linode_instance.delete()


@pytest.fixture
def create_linode_for_pass_reset(get_client):
    client = get_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    timestamp = str(int(time.time()))
    label = "TestSDK-" + timestamp

    linode_instance, password = client.linode.instance_create(
        "g5-standard-4", chosen_region, image="linode/debian9", label=label
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
def get_client():
    token = get_token()
    client = LinodeClient(token)
    return client


@pytest.fixture
def set_account_settings(get_client):
    client = get_client
    account_settings = client.account.settings()
    account_settings._populated = True
    account_settings.network_helper = True

    account_settings.save()


@pytest.fixture(scope="session")
def create_domain(get_client):
    client = get_client

    timestamp = str(int(time.time()))
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
def create_volume(get_client):
    client = get_client
    timestamp = str(int(time.time()))
    label = "TestSDK-" + timestamp

    volume = client.volume_create(label=label, region="ap-west")

    yield volume

    volume.delete()


@pytest.fixture
def create_tag(get_client):
    client = get_client

    timestamp = str(int(time.time()))
    label = "TestSDK-" + timestamp

    tag = client.tag_create(label=label)

    yield tag

    tag.delete()


@pytest.fixture
def create_nodebalancer(get_client):
    client = get_client

    timestamp = str(int(time.time()))
    label = "TestSDK-" + timestamp

    nodebalancer = client.nodebalancer_create(region="us-east", label=label)

    yield nodebalancer

    nodebalancer.delete()


@pytest.fixture
def create_longview_client(get_client):
    client = get_client
    timestamp = str(int(time.time()))
    label = "TestSDK-" + timestamp
    longview_client = client.longview.client_create(label=label)

    yield longview_client

    longview_client.delete()


@pytest.fixture
def upload_sshkey(get_client, ssh_key_gen):
    pub_key = ssh_key_gen[0]
    client = get_client
    key = client.profile.ssh_key_upload(pub_key, "IntTestSDK-sshkey")

    yield key

    key.delete()


@pytest.fixture
def create_ssh_keys_object_storage(get_client):
    client = get_client
    label = "TestSDK-obj-storage-key"
    key = client.object_storage.keys_create(label)

    yield key

    key.delete()


@pytest.fixture(scope="session")
def create_firewall(get_client):
    client = get_client
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
def create_oauth_client(get_client):
    client = get_client
    oauth_client = client.account.oauth_client_create(
        "test-oauth-client", "https://localhost/oauth/callback"
    )

    yield oauth_client

    oauth_client.delete()

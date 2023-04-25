import os
import time

import pytest

from linode_api4.linode_client import LinodeClient, LongviewSubscription

ENV_TOKEN_NAME = "LINODE_CLI_TOKEN"


def get_token():
    return os.environ.get(ENV_TOKEN_NAME, None)


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
def set_up_account(get_client):
    client = get_client
    account = client.account()

    account.first_name = "Test"
    account.last_name = "User"
    account.email = "test-123@linode.com"
    account.phone = "111-111-1111"
    account.address_1 = "3rd & Arch St"
    account.address_2 = "Unit 999"
    account.city = "Philadelphia"
    account.state = "PA"
    account.country = "US"
    account.zip = "19106"
    account.tax_id = "999-99-9999"

    account.save()


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

    yield domain

    domain.delete()


@pytest.fixture
def create_volume(get_client):
    client = get_client
    timestamp = str(int(time.time()))
    label = "TestSDK-" + timestamp

    volume = client.volume_create(label=label, region="us-east")

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

    nodebalancer = client.nodebalancer_create(region="us-east")

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


@pytest.fixture
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

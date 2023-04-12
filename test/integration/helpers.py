import pytest
import time
from linode_api4.linode_client import LinodeClient 

@pytest.fixture(scope="session")
def create_domain(get_client):
    client = get_client

    timestamp = str(int(time.time()))
    domain_addr = timestamp + "example.com"
    soa_email = "test-123@linode.com"

    domain = client.domain_create(domain=domain_addr, soa_email=soa_email)

    yield domain
    
    domain.delete()


@pytest.fixture(scope="session")
def create_volume(get_client):
    client = get_client
    timestamp = str(int(time.time()))
    label = "Test-label" + timestamp

    volume = client.volume_create(label=label, region='us-east')

    yield volume

    volume.delete()


@pytest.fixture(scope="session")
def create_tag(get_client):
    client = get_client

    timestamp = str(int(time.time()))
    label = "Test-label" + timestamp

    tag = client.tag_create(label=label)

    yield tag

    tag.delete()


@pytest.fixture(scope="session")
def create_nodebalancer(get_client):
    client = get_client

    timestamp = str(int(time.time()))
    label = "Test-label" + timestamp

    nodebalancer = client.nodebalancer_create(region='us-east')

    yield nodebalancer

    nodebalancer.delete()
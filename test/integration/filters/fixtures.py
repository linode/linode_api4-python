from test.integration.conftest import get_region
from test.integration.helpers import get_test_label

import pytest


@pytest.fixture(scope="package")
def domain_instance(test_linode_client):
    client = test_linode_client

    domain_addr = get_test_label(5) + "-example.com"
    soa_email = "dx-test-email@linode.com"

    domain = client.domain_create(domain=domain_addr, soa_email=soa_email)

    yield domain

    domain.delete()


@pytest.fixture(scope="package")
def lke_cluster_instance(test_linode_client):
    node_type = test_linode_client.linode.types()[1]  # g6-standard-1
    version = test_linode_client.lke.versions()[0]

    region = get_region(test_linode_client, {"Kubernetes", "Disk Encryption"})

    node_pools = test_linode_client.lke.node_pool(node_type, 3)
    label = get_test_label() + "_cluster"

    cluster = test_linode_client.lke.cluster_create(
        region, label, node_pools, version
    )

    yield cluster

    cluster.delete()

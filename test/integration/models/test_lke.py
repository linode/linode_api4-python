import re
from test.integration.helpers import (
    get_test_label,
    send_request_when_resource_available,
    wait_for_condition,
)

import pytest

from linode_api4.errors import ApiError
from linode_api4.objects import LKECluster, LKENodePool, LKENodePoolNode


@pytest.fixture(scope="session")
def lke_cluster(test_linode_client):
    node_type = test_linode_client.linode.types()[1]  # g6-standard-1
    version = test_linode_client.lke.versions()[0]
    region = test_linode_client.regions().first()
    node_pools = test_linode_client.lke.node_pool(node_type, 3)
    label = get_test_label() + "_cluster"

    cluster = test_linode_client.lke.cluster_create(
        region, label, node_pools, version
    )

    yield cluster

    cluster.delete()


def get_cluster_status(cluster: LKECluster, status: str):
    return cluster._raw_json["status"] == status


def get_node_status(cluster: LKECluster, status: str):
    node = cluster.pools[0].nodes[0]
    return node.status == status


@pytest.mark.smoke
def test_get_lke_clusters(test_linode_client, lke_cluster):
    cluster = test_linode_client.load(LKECluster, lke_cluster.id)

    assert cluster._raw_json == lke_cluster._raw_json


def test_get_lke_pool(test_linode_client, lke_cluster):
    pytest.skip("TPT-2511")
    cluster = lke_cluster

    pool = test_linode_client.load(LKENodePool, cluster.pools[0].id, cluster.id)

    assert cluster.pools[0]._raw_json == pool


def test_cluster_dashboard_url_view(lke_cluster):
    cluster = lke_cluster

    url = send_request_when_resource_available(
        300, cluster.cluster_dashboard_url_view
    )

    assert re.search("https://+", url)


def test_kubeconfig_delete(lke_cluster):
    cluster = lke_cluster

    res = send_request_when_resource_available(300, cluster.kubeconfig_delete)

    assert res is None


def test_lke_node_view(lke_cluster):
    cluster = lke_cluster
    node_id = cluster.pools[0].nodes[0].id

    node = cluster.node_view(node_id)

    assert node.status in ("ready", "not_ready")
    assert node.id == node_id
    assert node.instance_id


def test_lke_node_delete(lke_cluster):
    cluster = lke_cluster
    node_id = cluster.pools[0].nodes[0].id

    cluster.node_delete(node_id)

    with pytest.raises(ApiError) as err:
        cluster.node_view(node_id)
        assert "Not found" in str(err.json)


def test_lke_node_recycle(test_linode_client, lke_cluster):
    cluster = test_linode_client.load(LKECluster, lke_cluster.id)
    node = cluster.pools[0].nodes[0]
    node_id = cluster.pools[0].nodes[0].id

    send_request_when_resource_available(300, cluster.node_recycle, node_id)

    wait_for_condition(10, 300, get_node_status, cluster, "not_ready")

    node = cluster.pools[0].nodes[0]
    assert node.status == "not_ready"

    # wait for provisioning
    wait_for_condition(10, 300, get_node_status, cluster, "ready")

    node = cluster.pools[0].nodes[0]
    assert node.status == "ready"


def test_lke_cluster_nodes_recycle(test_linode_client, lke_cluster):
    cluster = lke_cluster

    send_request_when_resource_available(300, cluster.cluster_nodes_recycle)

    wait_for_condition(5, 300, get_node_status, cluster, "not_ready")

    node = cluster.pools[0].nodes[0]
    assert node.status == "not_ready"


def test_service_token_delete(lke_cluster):
    cluster = lke_cluster

    res = cluster.service_token_delete()

    assert res is None

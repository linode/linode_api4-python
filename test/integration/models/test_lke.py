import re
from test.integration.helpers import get_test_label, wait_for_condition

import pytest

from linode_api4.errors import ApiError
from linode_api4.objects import LKECluster, LKENodePool, LKENodePoolNode


@pytest.fixture(scope="session")
def create_lke_cluster(get_client):
    node_type = get_client.linode.types()[1]  # g6-standard-1
    version = get_client.lke.versions()[0]
    region = get_client.regions().first()
    node_pools = get_client.lke.node_pool(node_type, 3)
    label = get_test_label() + "_cluster"

    cluster = get_client.lke.cluster_create(region, label, node_pools, version)

    yield cluster

    cluster.delete()


def test_get_lke_clusters(get_client, create_lke_cluster):
    cluster = get_client.load(LKECluster, create_lke_cluster.id)

    assert cluster._raw_json == create_lke_cluster._raw_json


def test_get_lke_pool(get_client, create_lke_cluster):
    pytest.skip("client.load(LKENodePool, 123, 123) does not work")

    cluster = create_lke_cluster

    pool = get_client.load(LKENodePool, cluster.pools[0].id, cluster.id)

    assert cluster.pools[0]._raw_json == pool


def test_cluster_dashboard_url_view(create_lke_cluster):
    cluster = create_lke_cluster

    url = cluster.cluster_dashboard_url_view()

    assert re.search("http*://+", url)


def test_kubeconfig_delete(create_lke_cluster):
    cluster = create_lke_cluster

    cluster.kubeconfig_delete()


def test_lke_node_view(create_lke_cluster):
    cluster = create_lke_cluster
    node_id = cluster.pools[0].nodes[0].id

    node = cluster.node_view(node_id)

    assert node.status is "ready" or node.status is "not_ready"
    assert node.id == node_id
    assert node.instance_id


def test_lke_node_delete(create_lke_cluster):
    cluster = create_lke_cluster
    node_id = cluster.pools[0].nodes[0].id

    cluster.node_delete(node_id)

    with pytest.raises(ApiError) as err:
        cluster.node_view(node_id)
        assert "Not found" in str(err.json)


def test_lke_node_recycle(create_lke_cluster):
    cluster = create_lke_cluster
    node = cluster.pools[0].nodes[0]
    node_id = cluster.pools[0].nodes[0].id

    cluster.node_recycle(node_id)

    def get_status():
        node.status == "not_ready"

    wait_for_condition(5, 30, get_status)

    assert node.status == "not_ready"


def test_lke_cluster_nodes_recycle(create_lke_cluster):
    cluster = create_lke_cluster
    node = cluster.pools[0].nodes[0]

    cluster.cluster_nodes_recycle()

    def get_status():
        node.status == "not_ready"

    wait_for_condition(5, 30, get_status)

    for n in cluster.pools[0].nodes:
        assert n.status == "not_ready"


def test_lke_cluster_regenerate(create_lke_cluster):
    pytest.skip(
        "Skipping reason: '400: At least one of kubeconfig or servicetoken is required.'"
    )
    cluster = create_lke_cluster

    cluster.cluster_regenerate()


def test_service_token_delete(create_lke_cluster):
    pytest.skip(
        "Skipping reason: '400: At least one of kubeconfig or servicetoken is required.'"
    )
    cluster = create_lke_cluster

    cluster.service_token_delete()

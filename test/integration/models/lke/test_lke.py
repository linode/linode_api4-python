import base64
import re
from test.integration.conftest import get_region
from test.integration.helpers import (
    get_test_label,
    send_request_when_resource_available,
    wait_for_condition,
)
from typing import Any, Dict

import pytest

from linode_api4 import (
    LKEClusterControlPlaneACLAddressesOptions,
    LKEClusterControlPlaneACLOptions,
    LKEClusterControlPlaneOptions,
)
from linode_api4.common import RegionPrice
from linode_api4.errors import ApiError
from linode_api4.objects import (
    LKECluster,
    LKENodePool,
    LKENodePoolTaint,
    LKEType,
)


@pytest.fixture(scope="session")
def lke_cluster(test_linode_client):
    node_type = test_linode_client.linode.types()[1]  # g6-standard-1
    version = test_linode_client.lke.versions()[0]

    # TODO(LDE): Uncomment once LDE is available
    # region = get_region(test_linode_client, {"Kubernetes", "Disk Encryption"})
    region = get_region(test_linode_client, {"Kubernetes"})

    node_pools = test_linode_client.lke.node_pool(node_type, 3)
    label = get_test_label() + "_cluster"

    cluster = test_linode_client.lke.cluster_create(
        region, label, node_pools, version
    )

    yield cluster

    cluster.delete()


@pytest.fixture(scope="session")
def lke_cluster_with_acl(test_linode_client):
    node_type = test_linode_client.linode.types()[1]  # g6-standard-1
    version = test_linode_client.lke.versions()[0]
    region = get_region(test_linode_client, {"Kubernetes"})
    node_pools = test_linode_client.lke.node_pool(node_type, 1)
    label = get_test_label() + "_cluster"

    cluster = test_linode_client.lke.cluster_create(
        region,
        label,
        node_pools,
        version,
        control_plane=LKEClusterControlPlaneOptions(
            acl=LKEClusterControlPlaneACLOptions(
                enabled=True,
                addresses=LKEClusterControlPlaneACLAddressesOptions(
                    ipv4=["10.0.0.1/32"], ipv6=["1234::5678"]
                ),
            )
        ),
    )

    yield cluster

    cluster.delete()


# NOTE: This needs to be function-scoped because it is mutated in a test below.
@pytest.fixture(scope="function")
def lke_cluster_with_labels_and_taints(test_linode_client):
    node_type = test_linode_client.linode.types()[1]  # g6-standard-1
    version = test_linode_client.lke.versions()[0]

    region = get_region(test_linode_client, {"Kubernetes"})

    node_pools = test_linode_client.lke.node_pool(
        node_type,
        3,
        labels={
            "foo.example.com/test": "bar",
            "foo.example.com/test2": "test",
        },
        taints=[
            LKENodePoolTaint(
                key="foo.example.com/test", value="bar", effect="NoSchedule"
            ),
            {
                "key": "foo.example.com/test2",
                "value": "cool",
                "effect": "NoExecute",
            },
        ],
    )
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


@pytest.mark.smoke
def test_get_lke_pool(test_linode_client, lke_cluster):
    cluster = lke_cluster

    wait_for_condition(
        10,
        500,
        get_node_status,
        cluster,
        "ready",
    )

    pool = test_linode_client.load(LKENodePool, cluster.pools[0].id, cluster.id)

    def _to_comparable(p: LKENodePool) -> Dict[str, Any]:
        return {k: v for k, v in p._raw_json.items() if k not in {"nodes"}}

    assert _to_comparable(cluster.pools[0]) == _to_comparable(pool)

    # TODO(LDE): Uncomment once LDE is available
    # assert pool.disk_encryption == InstanceDiskEncryptionType.enabled


def test_cluster_dashboard_url_view(lke_cluster):
    cluster = lke_cluster

    url = send_request_when_resource_available(
        300, cluster.cluster_dashboard_url_view
    )

    assert re.search("https://+", url)


def test_get_and_delete_kubeconfig(lke_cluster):
    cluster = lke_cluster

    kubeconfig_encoded = cluster.kubeconfig

    kubeconfig_decoded = base64.b64decode(kubeconfig_encoded).decode("utf-8")

    assert "kind: Config" in kubeconfig_decoded

    assert "apiVersion:" in kubeconfig_decoded

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

    node_id = cluster.pools[0].nodes[0].id

    send_request_when_resource_available(300, cluster.node_recycle, node_id)

    wait_for_condition(10, 300, get_node_status, cluster, "not_ready")

    node = cluster.pools[0].nodes[0]
    assert node.status == "not_ready"

    # wait for provisioning
    wait_for_condition(
        10,
        500,
        get_node_status,
        test_linode_client.load(LKECluster, lke_cluster.id),
        "ready",
    )

    # Reload cluster
    cluster = test_linode_client.load(LKECluster, lke_cluster.id)

    node = cluster.pools[0].nodes[0]

    assert node.status == "ready"


def test_lke_cluster_nodes_recycle(test_linode_client, lke_cluster):
    cluster = lke_cluster

    send_request_when_resource_available(300, cluster.cluster_nodes_recycle)

    wait_for_condition(
        5,
        300,
        get_node_status,
        test_linode_client.load(LKECluster, cluster.id),
        "not_ready",
    )

    node_pool = test_linode_client.load(
        LKENodePool, cluster.pools[0].id, cluster.id
    )
    node = node_pool.nodes[0]
    assert node.status == "not_ready"


def test_service_token_delete(lke_cluster):
    cluster = lke_cluster

    res = cluster.service_token_delete()

    assert res is None


def test_lke_cluster_acl(lke_cluster_with_acl):
    cluster = lke_cluster_with_acl

    assert cluster.control_plane_acl.enabled
    assert cluster.control_plane_acl.addresses.ipv4 == ["10.0.0.1/32"]
    assert cluster.control_plane_acl.addresses.ipv6 == ["1234::5678/128"]

    acl = cluster.control_plane_acl_update(
        LKEClusterControlPlaneACLOptions(
            addresses=LKEClusterControlPlaneACLAddressesOptions(
                ipv4=["10.0.0.2/32"]
            )
        )
    )

    assert acl == cluster.control_plane_acl
    assert acl.addresses.ipv4 == ["10.0.0.2/32"]

    cluster.control_plane_acl_delete()

    assert not cluster.control_plane_acl.enabled


@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_lke_cluster_labels_and_taints(lke_cluster_with_labels_and_taints):
    pool = lke_cluster_with_labels_and_taints.pools[0]

    assert vars(pool.labels) == {
        "foo.example.com/test": "bar",
        "foo.example.com/test2": "test",
    }

    assert (
        LKENodePoolTaint(
            key="foo.example.com/test", value="bar", effect="NoSchedule"
        )
        in pool.taints
    )

    assert (
        LKENodePoolTaint(
            key="foo.example.com/test2", value="cool", effect="NoExecute"
        )
        in pool.taints
    )

    updated_labels = {
        "foo.example.com/test": "bar",
        "foo.example.com/test2": "cool",
    }

    updated_taints = [
        LKENodePoolTaint(
            key="foo.example.com/test", value="bar", effect="NoSchedule"
        ),
        {
            "key": "foo.example.com/test2",
            "value": "cool",
            "effect": "NoExecute",
        },
    ]

    pool.labels = updated_labels
    pool.taints = updated_taints

    pool.save()

    # Invalidate the pool so we can assert on the refreshed values
    pool.invalidate()

    assert vars(pool.labels) == updated_labels
    assert updated_taints[0] in pool.taints
    assert LKENodePoolTaint.from_json(updated_taints[1]) in pool.taints


def test_lke_types(test_linode_client):
    types = test_linode_client.lke.types()

    if len(types) > 0:
        for lke_type in types:
            assert type(lke_type) is LKEType
            assert lke_type.price.monthly is None or (
                isinstance(lke_type.price.monthly, (float, int))
                and lke_type.price.monthly >= 0
            )
            if len(lke_type.region_prices) > 0:
                region_price = lke_type.region_prices[0]
                assert type(region_price) is RegionPrice
                assert lke_type.price.monthly is None or (
                    isinstance(lke_type.price.monthly, (float, int))
                    and lke_type.price.monthly >= 0
                )

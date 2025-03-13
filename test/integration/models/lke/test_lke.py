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
    TieredKubeVersion,
)
from linode_api4.common import RegionPrice
from linode_api4.errors import ApiError
from linode_api4.objects import (
    LKECluster,
    LKENodePool,
    LKENodePoolTaint,
    LKEType,
)
from linode_api4.objects.linode import InstanceDiskEncryptionType


@pytest.fixture(scope="session")
def lke_cluster(test_linode_client):
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


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="session")
def lke_cluster_with_apl(test_linode_client):
    version = test_linode_client.lke.versions()[0]

    region = get_region(test_linode_client, {"Kubernetes", "Disk Encryption"})

    # NOTE: g6-dedicated-4 is the minimum APL-compatible Linode type
    node_pools = test_linode_client.lke.node_pool("g6-dedicated-4", 3)
    label = get_test_label() + "_cluster"

    cluster = test_linode_client.lke.cluster_create(
        region,
        label,
        node_pools,
        version,
        control_plane=LKEClusterControlPlaneOptions(
            high_availability=True,
        ),
        apl_enabled=True,
    )

    yield cluster

    cluster.delete()


@pytest.fixture(scope="session")
def lke_cluster_enterprise(test_linode_client):
    # We use the oldest version here so we can test upgrades
    version = sorted(
        v.id for v in test_linode_client.lke.tier("enterprise").versions()
    )[0]

    region = get_region(
        test_linode_client, {"Kubernetes Enterprise", "Disk Encryption"}
    )

    node_pools = test_linode_client.lke.node_pool(
        "g6-dedicated-2",
        3,
        k8s_version=version,
        update_strategy="rolling_update",
    )
    label = get_test_label() + "_cluster"

    cluster = test_linode_client.lke.cluster_create(
        region,
        label,
        node_pools,
        version,
        tier="enterprise",
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

    assert pool.disk_encryption == InstanceDiskEncryptionType.enabled


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
            enabled=True,
            addresses=LKEClusterControlPlaneACLAddressesOptions(
                ipv4=["10.0.0.2/32"]
            ),
        )
    )

    assert acl == cluster.control_plane_acl
    assert acl.addresses.ipv4 == ["10.0.0.2/32"]


def test_lke_cluster_update_acl_null_addresses(lke_cluster_with_acl):
    cluster = lke_cluster_with_acl

    # Addresses should not be included in the request if it's null,
    # else an error will be returned by the API.
    # See: TPT-3489
    acl = cluster.control_plane_acl_update(
        {"enabled": False, "addresses": None}
    )

    assert acl == cluster.control_plane_acl
    assert acl.addresses.ipv4 == []


def test_lke_cluster_disable_acl(lke_cluster_with_acl):
    cluster = lke_cluster_with_acl

    assert cluster.control_plane_acl.enabled

    acl = cluster.control_plane_acl_update(
        LKEClusterControlPlaneACLOptions(
            enabled=False,
        )
    )

    assert acl.enabled is False
    assert acl == cluster.control_plane_acl
    assert acl.addresses.ipv4 == []

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


@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_lke_cluster_with_apl(lke_cluster_with_apl):
    assert lke_cluster_with_apl.apl_enabled == True
    assert (
        lke_cluster_with_apl.apl_console_url
        == f"https://console.lke{lke_cluster_with_apl.id}.akamai-apl.net"
    )
    assert (
        lke_cluster_with_apl.apl_health_check_url
        == f"https://auth.lke{lke_cluster_with_apl.id}.akamai-apl.net/ready"
    )


def test_lke_cluster_enterprise(test_linode_client, lke_cluster_enterprise):
    lke_cluster_enterprise.invalidate()
    assert lke_cluster_enterprise.tier == "enterprise"

    pool = lke_cluster_enterprise.pools[0]
    assert str(pool.k8s_version) == lke_cluster_enterprise.k8s_version.id
    assert pool.update_strategy == "rolling_update"

    target_version = sorted(
        v.id for v in test_linode_client.lke.tier("enterprise").versions()
    )[0]
    pool.update_strategy = "on_recycle"
    pool.k8s_version = target_version

    pool.save()

    pool.invalidate()

    assert pool.k8s_version == target_version
    assert pool.update_strategy == "on_recycle"


def test_lke_tiered_versions(test_linode_client):
    def __assert_version(tier: str, version: TieredKubeVersion):
        assert version.tier == tier
        assert len(version.id) > 0

    standard_versions = test_linode_client.lke.tier("standard").versions()
    assert len(standard_versions) > 0

    standard_version = standard_versions[0]
    __assert_version("standard", standard_version)

    standard_version.invalidate()
    __assert_version("standard", standard_version)

    enterprise_versions = test_linode_client.lke.tier("enterprise").versions()
    assert len(enterprise_versions) > 0

    enterprise_version = enterprise_versions[0]
    __assert_version("enterprise", enterprise_version)

    enterprise_version.invalidate()
    __assert_version("enterprise", enterprise_version)


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

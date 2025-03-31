from datetime import datetime
from test.unit.base import ClientBaseCase
from unittest.mock import MagicMock

from linode_api4 import InstanceDiskEncryptionType, TieredKubeVersion
from linode_api4.objects import (
    LKECluster,
    LKEClusterControlPlaneACLAddressesOptions,
    LKEClusterControlPlaneACLOptions,
    LKEClusterControlPlaneOptions,
    LKENodePool,
)
from linode_api4.objects.lke import LKENodePoolNode, LKENodePoolTaint


class LKETest(ClientBaseCase):
    """
    Tests methods of the LKE class
    """

    def test_get_cluster(self):
        """
        Tests that the LKECluster object is properly generated.
        """

        cluster = LKECluster(self.client, 18881)

        self.assertEqual(cluster.id, 18881)
        self.assertEqual(
            cluster.created,
            datetime(year=2021, month=2, day=10, hour=23, minute=54, second=21),
        )
        self.assertEqual(
            cluster.updated,
            datetime(year=2021, month=2, day=10, hour=23, minute=54, second=21),
        )
        self.assertEqual(cluster.label, "example-cluster")
        self.assertEqual(cluster.tags, [])
        self.assertEqual(cluster.region.id, "ap-west")
        self.assertEqual(cluster.k8s_version.id, "1.19")
        self.assertTrue(cluster.control_plane.high_availability)
        self.assertTrue(cluster.apl_enabled)

    def test_get_pool(self):
        """
        Tests that the LKENodePool object is properly generated.
        """

        pool = LKENodePool(self.client, 456, 18881)

        assert pool.id == 456
        assert pool.cluster_id == 18881
        assert pool.type.id == "g6-standard-4"
        assert pool.disk_encryption == InstanceDiskEncryptionType.enabled

        assert pool.disks is not None
        assert pool.nodes is not None
        assert pool.autoscaler is not None
        assert pool.tags is not None

        assert pool.labels.foo == "bar"
        assert pool.labels.bar == "foo"

        assert isinstance(pool.taints[0], LKENodePoolTaint)
        assert pool.taints[0].key == "foo"
        assert pool.taints[0].value == "bar"
        assert pool.taints[0].effect == "NoSchedule"

    def test_cluster_dashboard_url_view(self):
        """
        Tests that you can submit a correct cluster dashboard url api request.
        """
        cluster = LKECluster(self.client, 18881)

        with self.mock_get("/lke/clusters/18881/dashboard") as m:
            result = cluster.cluster_dashboard_url_view()
            self.assertEqual(m.call_url, "/lke/clusters/18881/dashboard")
            self.assertEqual(result, "https://example.dashboard.linodelke.net")

    def test_kubeconfig_delete(self):
        """
        Tests that you can submit a correct kubeconfig delete api request.
        """
        cluster = LKECluster(self.client, 18881)

        with self.mock_delete() as m:
            cluster.kubeconfig_delete()
            self.assertEqual(m.call_url, "/lke/clusters/18881/kubeconfig")

    def test_node_view(self):
        """
        Tests that you can submit a correct node view api request.
        """
        cluster = LKECluster(self.client, 18881)

        with self.mock_get("/lke/clusters/18881/nodes/123456") as m:
            node = cluster.node_view(123456)
            self.assertEqual(m.call_url, "/lke/clusters/18881/nodes/123456")
            self.assertIsNotNone(node)
            self.assertEqual(node.id, "123456")
            self.assertEqual(node.instance_id, 456)
            self.assertEqual(node.status, "ready")

    def test_node_delete(self):
        """
        Tests that you can submit a correct node delete api request.
        """
        cluster = LKECluster(self.client, 18881)

        with self.mock_delete() as m:
            cluster.node_delete(1234)
            self.assertEqual(m.call_url, "/lke/clusters/18881/nodes/1234")

    def test_node_recycle(self):
        """
        Tests that you can submit a correct node recycle api request.
        """
        cluster = LKECluster(self.client, 18881)

        with self.mock_post({}) as m:
            cluster.node_recycle(1234)
            self.assertEqual(
                m.call_url, "/lke/clusters/18881/nodes/1234/recycle"
            )

    def test_cluster_nodes_recycle(self):
        """
        Tests that you can submit a correct cluster nodes recycle api request.
        """
        cluster = LKECluster(self.client, 18881)

        with self.mock_post({}) as m:
            cluster.cluster_nodes_recycle()
            self.assertEqual(m.call_url, "/lke/clusters/18881/recycle")

    def test_cluster_regenerate(self):
        """
        Tests that you can submit a correct cluster regenerate api request.
        """
        cluster = LKECluster(self.client, 18881)

        with self.mock_post({}) as m:
            cluster.cluster_regenerate()
            self.assertEqual(m.call_url, "/lke/clusters/18881/regenerate")

    def test_service_token_delete(self):
        """
        Tests that you can submit a correct service token delete api request.
        """
        cluster = LKECluster(self.client, 18881)

        with self.mock_delete() as m:
            cluster.service_token_delete()
            self.assertEqual(m.call_url, "/lke/clusters/18881/servicetoken")

    def test_load_node_pool(self):
        """
        Tests that an LKE Node Pool can be retrieved using LinodeClient.load(...)
        """
        pool = self.client.load(LKENodePool, 456, 18881)

        self.assertEqual(pool.id, 456)
        self.assertEqual(pool.cluster_id, 18881)
        self.assertEqual(pool.type.id, "g6-standard-4")
        self.assertIsNotNone(pool.disks)
        self.assertIsNotNone(pool.nodes)
        self.assertIsNotNone(pool.autoscaler)
        self.assertIsNotNone(pool.tags)

    def test_cluster_get_acl(self):
        """
        Tests that an LKE cluster can be created with a control plane ACL configuration.
        """
        cluster = LKECluster(self.client, 18881)

        with self.mock_get("lke/clusters/18881/control_plane_acl") as m:
            _ = cluster.control_plane_acl

            # Get the value again to pull from cache
            acl = cluster.control_plane_acl

            assert m.call_url == "/lke/clusters/18881/control_plane_acl"
            assert m.method == "get"

            # Ensure the endpoint was only called once
            assert m.called == 1

        assert acl.enabled
        assert acl.addresses.ipv4 == ["10.0.0.1/32"]
        assert acl.addresses.ipv6 == ["1234::5678"]

    def test_cluster_put_acl(self):
        """
        Tests that an LKE cluster can be created with a control plane ACL configuration.
        """
        cluster = LKECluster(self.client, 18881)

        with self.mock_put("lke/clusters/18881/control_plane_acl") as m:
            acl = cluster.control_plane_acl_update(
                LKEClusterControlPlaneACLOptions(
                    addresses=LKEClusterControlPlaneACLAddressesOptions(
                        ipv4=["10.0.0.2/32"],
                    )
                )
            )

            # Make sure the cache was updated
            assert cluster.control_plane_acl.dict == acl.dict

            assert m.call_url == "/lke/clusters/18881/control_plane_acl"
            assert m.method == "put"
            assert m.call_data == {
                "acl": {
                    "addresses": {
                        "ipv4": ["10.0.0.2/32"],
                    }
                }
            }

        assert acl.enabled
        assert acl.addresses.ipv4 == ["10.0.0.1/32"]

    def test_cluster_delete_acl(self):
        """
        Tests that an LKE cluster can be created with a control plane ACL configuration.
        """
        cluster = LKECluster(self.client, 18881)

        with self.mock_delete() as m:
            cluster.control_plane_acl_delete()

            # Make sure the cache was cleared
            assert not hasattr(cluster, "_control_plane_acl")

            assert m.call_url == "/lke/clusters/18881/control_plane_acl"
            assert m.method == "delete"

        # We expect a GET request to be made when accessing `control_plane_acl`
        # because the cached value has been invalidated
        with self.mock_get("lke/clusters/18881/control_plane_acl") as m:
            cluster.control_plane_acl

            assert m.call_url == "/lke/clusters/18881/control_plane_acl"
            assert m.method == "get"

    def test_lke_node_pool_update(self):
        """
        Tests that an LKE Node Pool can be properly updated.
        """
        pool = LKENodePool(self.client, 456, 18881)

        pool.tags = ["foobar"]
        pool.count = 5
        pool.autoscaler = {
            "enabled": True,
            "min": 2,
            "max": 10,
        }
        pool.labels = {"updated-key": "updated-value"}
        pool.taints = [
            LKENodePoolTaint(
                key="updated-key", value="updated-value", effect="NoExecute"
            )
        ]

        with self.mock_put("lke/clusters/18881/pools/456") as m:
            pool.save()

            assert m.call_data == {
                "tags": ["foobar"],
                "count": 5,
                "autoscaler": {
                    "enabled": True,
                    "min": 2,
                    "max": 10,
                },
                "labels": {
                    "updated-key": "updated-value",
                },
                "taints": [
                    {
                        "key": "updated-key",
                        "value": "updated-value",
                        "effect": "NoExecute",
                    }
                ],
            }

    def test_cluster_create_with_labels_and_taints(self):
        """
        Tests that an LKE cluster can be created with labels and taints.
        """

        with self.mock_post("lke/clusters") as m:
            self.client.lke.cluster_create(
                "us-mia",
                "test-acl-cluster",
                [
                    self.client.lke.node_pool(
                        "g6-nanode-1",
                        3,
                        labels={
                            "foo": "bar",
                        },
                        taints=[
                            LKENodePoolTaint(
                                key="a", value="b", effect="NoSchedule"
                            ),
                            {"key": "b", "value": "a", "effect": "NoSchedule"},
                        ],
                    )
                ],
                "1.29",
            )

            assert m.call_data["node_pools"][0] == {
                "type": "g6-nanode-1",
                "count": 3,
                "labels": {"foo": "bar"},
                "taints": [
                    {"key": "a", "value": "b", "effect": "NoSchedule"},
                    {"key": "b", "value": "a", "effect": "NoSchedule"},
                ],
            }

    def test_cluster_create_with_apl(self):
        """
        Tests that an LKE cluster can be created with APL enabled.
        """

        with self.mock_post("lke/clusters") as m:
            cluster = self.client.lke.cluster_create(
                "us-mia",
                "test-aapl-cluster",
                [
                    self.client.lke.node_pool(
                        "g6-dedicated-4",
                        3,
                    )
                ],
                "1.29",
                apl_enabled=True,
                control_plane=LKEClusterControlPlaneOptions(
                    high_availability=True,
                ),
            )

            assert m.call_data["apl_enabled"] == True
            assert m.call_data["control_plane"]["high_availability"] == True

        assert (
            cluster.apl_console_url == "https://console.lke18881.akamai-apl.net"
        )

        assert (
            cluster.apl_health_check_url
            == "https://auth.lke18881.akamai-apl.net/ready"
        )

    def test_populate_with_taints(self):
        """
        Tests that LKENodePool correctly handles a list of LKENodePoolTaint and Dict objects.
        """
        self.client = MagicMock()
        self.pool = LKENodePool(self.client, 456, 18881)

        self.pool._populate(
            {
                "taints": [
                    LKENodePoolTaint(
                        key="wow", value="cool", effect="NoExecute"
                    ),
                    {
                        "key": "foo",
                        "value": "bar",
                        "effect": "NoSchedule",
                    },
                ],
            }
        )

        assert len(self.pool.taints) == 2

        assert self.pool.taints[0].dict == {
            "key": "wow",
            "value": "cool",
            "effect": "NoExecute",
        }

        assert self.pool.taints[1].dict == {
            "key": "foo",
            "value": "bar",
            "effect": "NoSchedule",
        }

    def test_populate_with_node_objects(self):
        """
        Tests that LKENodePool correctly handles a list of LKENodePoolNode objects.
        """
        self.client = MagicMock()
        self.pool = LKENodePool(self.client, 456, 18881)

        node1 = LKENodePoolNode(
            self.client, {"id": "node1", "instance_id": 101, "status": "active"}
        )
        node2 = LKENodePoolNode(
            self.client,
            {"id": "node2", "instance_id": 102, "status": "inactive"},
        )
        self.pool._populate({"nodes": [node1, node2]})

        self.assertEqual(len(self.pool.nodes), 2)
        self.assertIsInstance(self.pool.nodes[0], LKENodePoolNode)
        self.assertIsInstance(self.pool.nodes[1], LKENodePoolNode)
        self.assertEqual(self.pool.nodes[0].id, "node1")
        self.assertEqual(self.pool.nodes[1].id, "node2")

    def test_populate_with_node_dicts(self):
        """
        Tests that LKENodePool correctly handles a list of node dictionaries.
        """
        self.client = MagicMock()
        self.pool = LKENodePool(self.client, 456, 18881)

        node_dict1 = {"id": "node3", "instance_id": 103, "status": "pending"}
        node_dict2 = {"id": "node4", "instance_id": 104, "status": "failed"}
        self.pool._populate({"nodes": [node_dict1, node_dict2]})

        assert len(self.pool.nodes) == 2

        assert isinstance(self.pool.nodes[0], LKENodePoolNode)
        assert isinstance(self.pool.nodes[1], LKENodePoolNode)

        assert self.pool.nodes[0].id == "node3"
        assert self.pool.nodes[1].id == "node4"

    def test_populate_with_node_ids(self):
        """
        Tests that LKENodePool correctly handles a list of node IDs.
        """
        self.client = MagicMock()
        self.pool = LKENodePool(self.client, 456, 18881)

        node_id1 = "node5"
        node_id2 = "node6"

        # Mock instances creation
        self.client.load = MagicMock(
            side_effect=[
                LKENodePoolNode(
                    self.client,
                    {"id": "node5", "instance_id": 105, "status": "active"},
                ),
                LKENodePoolNode(
                    self.client,
                    {"id": "node6", "instance_id": 106, "status": "inactive"},
                ),
            ]
        )

        self.pool._populate({"nodes": [node_id1, node_id2]})

        assert len(self.pool.nodes) == 2

        assert isinstance(self.pool.nodes[0], LKENodePoolNode)
        assert isinstance(self.pool.nodes[1], LKENodePoolNode)

        assert self.pool.nodes[0].id == "node5"
        assert self.pool.nodes[1].id == "node6"

    def test_populate_with_mixed_types(self):
        """
        Tests that LKENodePool correctly handles a mixed list of node objects, dicts, and IDs.
        """
        self.client = MagicMock()
        self.pool = LKENodePool(self.client, 456, 18881)

        node1 = LKENodePoolNode(
            self.client, {"id": "node7", "instance_id": 107, "status": "active"}
        )
        node_dict = {"id": "node8", "instance_id": 108, "status": "inactive"}
        node_id = "node9"
        # Mock instances creation
        self.client.load = MagicMock(
            side_effect=[
                LKENodePoolNode(
                    self.client,
                    {"id": "node9", "instance_id": 109, "status": "pending"},
                )
            ]
        )
        self.pool._populate({"nodes": [node1, node_dict, node_id]})

        assert len(self.pool.nodes) == 3
        assert isinstance(self.pool.nodes[0], LKENodePoolNode)
        assert isinstance(self.pool.nodes[1], LKENodePoolNode)
        assert isinstance(self.pool.nodes[2], LKENodePoolNode)
        assert self.pool.nodes[0].id == "node7"
        assert self.pool.nodes[1].id == "node8"
        assert self.pool.nodes[2].id == "node9"

    def test_cluster_create_acl_null_addresses(self):
        with self.mock_post("lke/clusters") as m:
            self.client.lke.cluster_create(
                region="us-mia",
                label="foobar",
                kube_version="1.32",
                node_pools=[self.client.lke.node_pool("g6-standard-1", 3)],
                control_plane={
                    "acl": {
                        "enabled": False,
                        "addresses": None,
                    }
                },
            )

            # Addresses should not be included in the API request if it's null
            # See: TPT-3489
            assert m.call_data["control_plane"] == {
                "acl": {
                    "enabled": False,
                }
            }

    def test_cluster_update_acl_null_addresses(self):
        cluster = LKECluster(self.client, 18881)

        with self.mock_put("lke/clusters/18881/control_plane_acl") as m:
            cluster.control_plane_acl_update(
                {
                    "enabled": True,
                    "addresses": None,
                }
            )

            # Addresses should not be included in the API request if it's null
            # See: TPT-3489
            assert m.call_data == {"acl": {"enabled": True}}

    def test_cluster_enterprise(self):
        cluster = LKECluster(self.client, 18882)

        assert cluster.tier == "enterprise"
        assert cluster.k8s_version.id == "1.31.1+lke1"

        pool = LKENodePool(self.client, 789, 18882)
        assert pool.k8s_version == "1.31.1+lke1"
        assert pool.update_strategy == "rolling_update"

    def test_lke_tiered_version(self):
        version = TieredKubeVersion(self.client, "1.32", "standard")

        assert version.id == "1.32"

        # Ensure the version is properly refreshed
        version.invalidate()

        assert version.id == "1.32"

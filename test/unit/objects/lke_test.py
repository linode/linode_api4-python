from datetime import datetime
from test.unit.base import ClientBaseCase

from linode_api4.objects import (
    LKECluster,
    LKEClusterControlPlaneACLAddressesOptions,
    LKEClusterControlPlaneACLOptions,
    LKEClusterControlPlaneOptions,
    LKENodePool,
)


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

    def test_get_pool(self):
        """
        Tests that the LKENodePool object is properly generated.
        """

        pool = LKENodePool(self.client, 456, 18881)

        self.assertEqual(pool.id, 456)
        self.assertEqual(pool.cluster_id, 18881)
        self.assertEqual(pool.type.id, "g6-standard-4")
        self.assertIsNotNone(pool.disks)
        self.assertIsNotNone(pool.nodes)
        self.assertIsNotNone(pool.autoscaler)
        self.assertIsNotNone(pool.tags)

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
            self.assertEqual(node.instance_id, 123458)
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

    def test_cluster_create_with_acl(self):
        """
        Tests that an LKE cluster can be created with a control plane ACL configuration.
        """

        with self.mock_post("lke/clusters") as m:
            self.client.lke.cluster_create(
                "us-mia",
                "test-acl-cluster",
                [self.client.lke.node_pool("g6-nanode-1", 3)],
                "1.29",
                control_plane=LKEClusterControlPlaneOptions(
                    acl=LKEClusterControlPlaneACLOptions(
                        enabled=True,
                        addresses=LKEClusterControlPlaneACLAddressesOptions(
                            ipv4=["10.0.0.1/32"], ipv6=["1234::5678"]
                        ),
                    )
                ),
            )

            assert "high_availability" not in m.call_data["control_plane"]
            assert m.call_data["control_plane"]["acl"]["enabled"]
            assert m.call_data["control_plane"]["acl"]["addresses"]["ipv4"] == [
                "10.0.0.1/32"
            ]
            assert m.call_data["control_plane"]["acl"]["addresses"]["ipv6"] == [
                "1234::5678"
            ]

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

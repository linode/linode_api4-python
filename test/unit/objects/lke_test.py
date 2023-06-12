from datetime import datetime
from test.unit.base import ClientBaseCase

from linode_api4.objects import LKECluster, LKENodePool


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

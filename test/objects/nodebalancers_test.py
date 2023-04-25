from test.base import ClientBaseCase

from linode_api4.objects import (
    NodeBalancer,
    NodeBalancerConfig,
    NodeBalancerNode,
)
from linode_api4.objects.base import MappedObject


class NodeBalancerConfigTest(ClientBaseCase):
    """
    Tests methods of the NodeBalancerConfig class
    """

    def test_get_config(self):
        """
        Tests that a config is loaded correctly by ID
        """
        config = NodeBalancerConfig(self.client, 65432, 123456)
        self.assertEqual(config._populated, False)

        self.assertEqual(config.port, 80)
        self.assertEqual(config._populated, True)

        self.assertEqual(config.check, "connection")
        self.assertEqual(config.protocol, "http")
        self.assertEqual(config.check_attempts, 2)
        self.assertEqual(config.stickiness, "table")
        self.assertEqual(config.check_interval, 5)
        self.assertEqual(config.check_body, "")
        self.assertEqual(config.check_passive, True)
        self.assertEqual(config.algorithm, "roundrobin")
        self.assertEqual(config.check_timeout, 3)
        self.assertEqual(config.check_path, "/")
        self.assertEqual(config.ssl_cert, None)
        self.assertEqual(config.ssl_commonname, "")
        self.assertEqual(config.nodebalancer_id, 123456)
        self.assertEqual(config.cipher_suite, "recommended")
        self.assertEqual(config.ssl_key, None)
        self.assertEqual(config.nodes_status.up, 0)
        self.assertEqual(config.nodes_status.down, 0)
        self.assertEqual(config.ssl_fingerprint, "")
        self.assertEqual(config.proxy_protocol, "none")


class NodeBalancerNodeTest(ClientBaseCase):
    """
    Tests methods of the NodeBalancerNode class
    """

    def test_get_node(self):
        """
        Tests that a node is loaded correctly by ID
        """
        node = NodeBalancerNode(self.client, 54321, (65432, 123456))
        self.assertEqual(node._populated, False)

        self.assertEqual(node.weight, 50)
        self.assertEqual(node._populated, True)

        self.assertEqual(node.id, 54321)
        self.assertEqual(node.address, "192.168.210.120")
        self.assertEqual(node.label, "node54321")
        self.assertEqual(node.status, "UP")
        self.assertEqual(node.mode, "accept")
        self.assertEqual(node.config_id, 65432)
        self.assertEqual(node.nodebalancer_id, 123456)

    def test_create_node(self):
        """
        Tests that a node can be created
        """
        with self.mock_post(
            "nodebalancers/123456/configs/65432/nodes/54321"
        ) as m:
            config = NodeBalancerConfig(self.client, 65432, 123456)
            node = config.node_create(
                "node54321", "192.168.210.120", weight=50, mode="accept"
            )

            self.assertIsNotNone(node)
            self.assertEqual(node.id, 54321)
            self.assertEqual(
                m.call_url, "/nodebalancers/123456/configs/65432/nodes"
            )
            self.assertEqual(
                m.call_data,
                {
                    "label": "node54321",
                    "address": "192.168.210.120",
                    "weight": 50,
                    "mode": "accept",
                },
            )

    def test_update_node(self):
        """
        Tests that a node can be updated
        """
        with self.mock_put(
            "nodebalancers/123456/configs/65432/nodes/54321"
        ) as m:
            node = self.client.load(NodeBalancerNode, 54321, (65432, 123456))
            node.label = "ThisNewLabel"
            node.weight = 60
            node.mode = "drain"
            node.address = "192.168.210.121"
            node.save()

            self.assertEqual(
                m.call_url, "/nodebalancers/123456/configs/65432/nodes/54321"
            )
            self.assertEqual(
                m.call_data,
                {
                    "label": "ThisNewLabel",
                    "address": "192.168.210.121",
                    "mode": "drain",
                    "weight": 60,
                },
            )

    def test_delete_node(self):
        """
        Tests that deleting a node creates the correct api request.
        """
        with self.mock_delete() as m:
            node = NodeBalancerNode(self.client, 54321, (65432, 123456))
            node.delete()

            self.assertEqual(
                m.call_url, "/nodebalancers/123456/configs/65432/nodes/54321"
            )

    def test_config_rebuild(self):
        """
        Test that you can rebuild the cofig of a node balancer.
        """
        config_rebuild_url = "/nodebalancers/12345/configs/4567/rebuild"
        with self.mock_post(config_rebuild_url) as m:
            nb = NodeBalancer(self.client, 12345)
            nodes = [
                {
                    "id": 54321,
                    "address": "192.168.210.120:80",
                    "label": "node1",
                    "weight": 50,
                    "mode": "accept",
                }
            ]

            result = nb.config_rebuild(
                4567,
                nodes,
                port=1234,
                protocol="https",
                algorithm="roundrobin",
            )
            self.assertIsNotNone(result)
            self.assertEqual(result.id, 4567)
            self.assertEqual(result.nodebalancer_id, 12345)
            self.assertEqual(m.call_url, config_rebuild_url)
            self.assertEqual(
                m.call_data,
                {
                    "port": 1234,
                    "protocol": "https",
                    "algorithm": "roundrobin",
                    "nodes": [
                        {
                            "id": 54321,
                            "address": "192.168.210.120:80",
                            "label": "node1",
                            "weight": 50,
                            "mode": "accept",
                        },
                    ],
                },
            )

    def test_statistics(self):
        """
        Test that you can get the statistics about the requested NodeBalancer.
        """
        statistics_url = "/nodebalancers/12345/stats"
        with self.mock_get(statistics_url) as m:
            nb = NodeBalancer(self.client, 12345)
            result = nb.statistics()

            self.assertIsNotNone(result)
            self.assertEqual(
                result.title,
                "linode.com - balancer12345 (12345) - day (5 min avg)",
            )
            self.assertEqual(m.call_url, statistics_url)

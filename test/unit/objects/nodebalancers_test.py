from test.unit.base import ClientBaseCase

from linode_api4.objects import (
    NodeBalancer,
    NodeBalancerConfig,
    NodeBalancerNode,
    NodeBalancerVPCConfig,
)


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

        config_udp = NodeBalancerConfig(self.client, 65431, 123456)
        self.assertEqual(config_udp.protocol, "udp")
        self.assertEqual(config_udp.udp_check_port, 12345)

    def test_update_config_udp(self):
        """
        Tests that a config with a protocol of udp can be updated and that cipher suite is properly excluded in save()
        """
        with self.mock_put("nodebalancers/123456/configs/65431") as m:
            config = self.client.load(NodeBalancerConfig, 65431, 123456)
            config.udp_check_port = 54321
            config.save()

            self.assertEqual(m.call_url, "/nodebalancers/123456/configs/65431")
            self.assertEqual(m.call_data["udp_check_port"], 54321)
            self.assertNotIn("cipher_suite", m.call_data)


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

        node_udp = NodeBalancerNode(self.client, 12345, (65432, 123456))
        self.assertEqual(node_udp.mode, "none")

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


class NodeBalancerTest(ClientBaseCase):
    def test_update(self):
        """
        Test that you can update a NodeBalancer.
        """
        nb = NodeBalancer(self.client, 123456)
        nb.label = "updated-label"
        nb.client_conn_throttle = 7
        nb.tags = ["foo", "bar"]

        with self.mock_put("nodebalancers/123456") as m:
            nb.save()
            self.assertEqual(m.call_url, "/nodebalancers/123456")
            self.assertEqual(
                m.call_data,
                {
                    "label": "updated-label",
                    "client_conn_throttle": 7,
                    "tags": ["foo", "bar"],
                },
            )

    def test_locks_not_in_put(self):
        """
        Test that locks are not included in PUT request when updating a NodeBalancer.
        Locks are managed through the separate /v4/locks endpoint.
        """
        nb = NodeBalancer(self.client, 123456)
        # Access locks to ensure it's loaded
        self.assertEqual(nb.locks, ["cannot_delete_with_subresources"])

        nb.label = "new-label"

        with self.mock_put("nodebalancers/123456") as m:
            nb.save()
            self.assertEqual(m.call_url, "/nodebalancers/123456")
            # Verify locks is NOT in the PUT data
            self.assertNotIn("locks", m.call_data)
            self.assertEqual(m.call_data["label"], "new-label")

    def test_firewalls(self):
        """
        Test that you can get the firewalls for the requested NodeBalancer.
        """
        nb = NodeBalancer(self.client, 12345)
        firewalls_url = "/nodebalancers/12345/firewalls"

        with self.mock_get(firewalls_url) as m:
            result = nb.firewalls()
            self.assertEqual(m.call_url, firewalls_url)
            self.assertEqual(len(result), 1)

    def test_config_rebuild(self):
        """
        Test that you can rebuild the config of a node balancer.
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

    def test_list_nodebalancers(self):
        """
        Test that you can list all NodeBalancers.
        """
        nbs = self.client.nodebalancers()

        self.assertEqual(len(nbs), 2)

        self.assertEqual(nbs[0].id, 123456)
        self.assertEqual(nbs[0].label, "balancer123456")
        self.assertEqual(nbs[0].type, "common")
        self.assertEqual(nbs[0].lke_cluster.id, 1234)
        self.assertEqual(nbs[0].lke_cluster.type, "lkecluster")
        self.assertEqual(nbs[0].lke_cluster.label, "test-cluster")
        self.assertEqual(nbs[0].lke_cluster.url, "/v4/lke/clusters/1234")
        self.assertEqual(nbs[0].frontend_address_type, "vpc")
        self.assertEqual(nbs[0].frontend_vpc_subnet_id, 5555)

        self.assertEqual(nbs[1].id, 123457)
        self.assertEqual(nbs[1].label, "balancer123457")
        self.assertEqual(nbs[1].type, "premium_40gb")
        self.assertEqual(nbs[1].lke_cluster, None)
        self.assertEqual(nbs[1].frontend_address_type, "vpc")
        self.assertEqual(nbs[1].frontend_vpc_subnet_id, 6666)

    def test_get_nodebalancer(self):
        """
        Test that you can get a single NodeBalancer by ID.
        """
        nb = NodeBalancer(self.client, 123456)

        self.assertEqual(nb.id, 123456)
        self.assertEqual(nb.label, "balancer123456")
        self.assertEqual(nb.type, "common")
        self.assertEqual(nb.lke_cluster.id, 1234)
        self.assertEqual(nb.lke_cluster.type, "lkecluster")
        self.assertEqual(nb.lke_cluster.label, "test-cluster")
        self.assertEqual(nb.lke_cluster.url, "/v4/lke/clusters/1234")
        self.assertEqual(nb.frontend_address_type, "vpc")
        self.assertEqual(nb.frontend_vpc_subnet_id, 5555)

    def test_vpcs(self):
        """
        Test that you can list VPC configurations for a NodeBalancer.
        """
        vpcs_url = "/nodebalancers/12345/vpcs"
        with self.mock_get(vpcs_url) as m:
            nb = NodeBalancer(self.client, 12345)
            result = nb.vpcs()

            self.assertEqual(m.call_url, vpcs_url)
            self.assertEqual(len(result), 2)

            self.assertIsInstance(result[0], NodeBalancerVPCConfig)
            self.assertEqual(result[0].id, 99)
            self.assertEqual(result[0].subnet_id, 5555)
            self.assertEqual(result[0].vpc_id, 111)
            self.assertEqual(result[0].ipv4_range, "10.100.5.0/24")
            self.assertEqual(result[0].ipv6_range, "2001:db8::/64")
            self.assertEqual(result[0].purpose, "frontend")

            self.assertIsInstance(result[1], NodeBalancerVPCConfig)
            self.assertEqual(result[1].id, 100)
            self.assertEqual(result[1].subnet_id, 5556)
            self.assertEqual(result[1].vpc_id, 112)
            self.assertEqual(result[1].ipv4_range, "10.100.6.0/24")
            self.assertEqual(result[1].ipv6_range, "2001:db8:1::/64")
            self.assertEqual(result[1].purpose, "backend")

    def test_vpc(self):
        """
        Test that you can get a single VPC configuration for a NodeBalancer.
        """
        vpc_url = "/nodebalancers/12345/vpcs/99"
        with self.mock_get(vpc_url) as m:
            nb = NodeBalancer(self.client, 12345)
            result = nb.vpc(99)

            self.assertEqual(m.call_url, vpc_url)
            self.assertIsInstance(result, NodeBalancerVPCConfig)
            self.assertEqual(result.id, 99)
            self.assertEqual(result.subnet_id, 5555)
            self.assertEqual(result.vpc_id, 111)
            self.assertEqual(result.ipv4_range, "10.100.5.0/24")
            self.assertEqual(result.ipv6_range, "2001:db8::/64")
            self.assertEqual(result.purpose, "frontend")

    def test_backend_vpcs(self):
        """
        Test that you can list backend VPC configurations for a NodeBalancer.
        """
        backend_vpcs_url = "/nodebalancers/12345/backend_vpcs"
        with self.mock_get(backend_vpcs_url) as m:
            nb = NodeBalancer(self.client, 12345)
            result = nb.backend_vpcs()

            self.assertEqual(m.call_url, backend_vpcs_url)
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], NodeBalancerVPCConfig)
            self.assertEqual(result[0].id, 101)
            self.assertEqual(result[0].subnet_id, 6666)
            self.assertEqual(result[0].vpc_id, 222)
            self.assertEqual(result[0].ipv4_range, "10.200.1.0/24")
            self.assertEqual(result[0].ipv6_range, "2001:db8:2::/64")
            self.assertEqual(result[0].purpose, "backend")

    def test_frontend_vpcs(self):
        """
        Test that you can list frontend VPC configurations for a NodeBalancer.
        """
        frontend_vpcs_url = "/nodebalancers/12345/frontend_vpcs"
        with self.mock_get(frontend_vpcs_url) as m:
            nb = NodeBalancer(self.client, 12345)
            result = nb.frontend_vpcs()

            self.assertEqual(m.call_url, frontend_vpcs_url)
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], NodeBalancerVPCConfig)
            self.assertEqual(result[0].id, 99)
            self.assertEqual(result[0].subnet_id, 5555)
            self.assertEqual(result[0].vpc_id, 111)
            self.assertEqual(result[0].ipv4_range, "10.100.5.0/24")
            self.assertEqual(result[0].ipv6_range, "2001:db8::/64")
            self.assertEqual(result[0].purpose, "frontend")

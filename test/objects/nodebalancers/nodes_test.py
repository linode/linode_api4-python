from datetime import datetime

from test.base import ClientBaseCase
from linode_api.objects.base import MappedObject

from linode_api.objects import NodeBalancerConfig, NodeBalancerNode


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
        with self.mock_post('nodebalancers/123456/configs/65432/nodes/54321') as m:
            config = NodeBalancerConfig(self.client, 65432, 123456)
            node = config.node_create('node54321', '192.168.210.120',
                weight=50, mode='accept')

            self.assertIsNotNone(node)
            self.assertEqual(node.id, 54321)
            self.assertEqual(m.call_url, '/nodebalancers/123456/configs/65432/nodes')
            self.assertEqual(m.call_data, {
                "label": "node54321",
                "address": "192.168.210.120",
                "weight": 50,
                "mode": "accept"
            })

    def test_update_node(self):
        """
        Tests that a node can be updated
        """
        with self.mock_put('nodebalancers/123456/configs/65432/nodes/54321') as m:
            node = NodeBalancerNode(self.client, 54321, (65432, 123456))
            node.label = "ThisNewLabel"
            node.weight = 60
            node.mode = "drain"
            node.address = "192.168.210.121"
            node.save()

            self.assertEqual(m.call_url, '/nodebalancers/123456/configs/65432/nodes/54321')
            self.assertEqual(m.call_data, {
                "label": "ThisNewLabel",
                "address": "192.168.210.121",
                "mode": "drain",
                "weight": 60
            })

    def test_delete_node(self):
        """
        Tests that deleting a node creates the correct api request.
        """
        with self.mock_delete() as m:
            node = NodeBalancerNode(self.client, 54321, (65432, 123456))
            node.delete()

            self.assertEqual(m.call_url, '/nodebalancers/123456/configs/65432/nodes/54321')

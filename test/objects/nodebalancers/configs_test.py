from datetime import datetime

from test.base import ClientBaseCase
from linode.objects.base import MappedObject

from linode.objects import NodeBalancerConfig


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

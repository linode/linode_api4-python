from test.unit.base import ClientBaseCase

from linode_api4.objects import Firewall, FirewallDevice


class FirewallTest(ClientBaseCase):
    """
    Tests methods of the Firewall class
    """

    def test_get_rules(self):
        """
        Test that the rules can be retrieved from a Firewall
        """
        firewall = Firewall(self.client, 123)
        rules = firewall.rules

        self.assertEqual(len(rules.inbound), 0)
        self.assertEqual(rules.inbound_policy, "DROP")
        self.assertEqual(len(rules.outbound), 0)
        self.assertEqual(rules.outbound_policy, "DROP")

    def test_update_rules(self):
        """
        Test that the rules can be updated for a Firewall
        """

        firewall = Firewall(self.client, 123)

        with self.mock_put("networking/firewalls/123/rules") as m:
            new_rules = {
                "inbound": [
                    {
                        "action": "ACCEPT",
                        "addresses": {
                            "ipv4": ["0.0.0.0/0"],
                            "ipv6": ["ff00::/8"],
                        },
                        "description": "A really cool firewall rule.",
                        "label": "really-cool-firewall-rule",
                        "ports": "80",
                        "protocol": "TCP",
                    }
                ],
                "inbound_policy": "ALLOW",
                "outbound": [],
                "outbound_policy": "ALLOW",
            }

            firewall.update_rules(new_rules)

            self.assertEqual(m.method, "put")
            self.assertEqual(m.call_url, "/networking/firewalls/123/rules")

            self.assertEqual(m.call_data, new_rules)


class FirewallDevicesTest(ClientBaseCase):
    """
    Tests methods of Firewall devices
    """

    def test_get_devices(self):
        """
        Tests that devices can be pulled from a firewall
        """
        firewall = Firewall(self.client, 123)
        self.assertEqual(len(firewall.devices), 1)

    def test_get_device(self):
        """
        Tests that a device is loaded correctly by ID
        """
        device = FirewallDevice(self.client, 123, 123)
        self.assertEqual(device._populated, False)

        self.assertEqual(device.id, 123)
        self.assertEqual(device.entity.id, 123)
        self.assertEqual(device.entity.label, "my-linode")
        self.assertEqual(device.entity.type, "linode")
        self.assertEqual(device.entity.url, "/v4/linode/instances/123")

        self.assertEqual(device._populated, True)

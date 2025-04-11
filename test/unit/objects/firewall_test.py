from test.unit.base import ClientBaseCase

from linode_api4 import FirewallTemplate, MappedObject
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


class FirewallTemplatesTest(ClientBaseCase):
    @staticmethod
    def assert_rules(rules: MappedObject):
        assert rules.outbound_policy == "DROP"
        assert len(rules.outbound) == 1

        assert rules.inbound_policy == "DROP"
        assert len(rules.inbound) == 1

        outbound_rule = rules.outbound[0]
        assert outbound_rule.action == "ACCEPT"
        assert outbound_rule.addresses.ipv4[0] == "192.0.2.0/24"
        assert outbound_rule.addresses.ipv4[1] == "198.51.100.2/32"
        assert outbound_rule.addresses.ipv6[0] == "2001:DB8::/128"
        assert outbound_rule.description == "test"
        assert outbound_rule.label == "test-rule"
        assert outbound_rule.ports == "22-24, 80, 443"
        assert outbound_rule.protocol == "TCP"

        inbound_rule = rules.outbound[0]
        assert inbound_rule.action == "ACCEPT"
        assert inbound_rule.addresses.ipv4[0] == "192.0.2.0/24"
        assert inbound_rule.addresses.ipv4[1] == "198.51.100.2/32"
        assert inbound_rule.addresses.ipv6[0] == "2001:DB8::/128"
        assert inbound_rule.description == "test"
        assert inbound_rule.label == "test-rule"
        assert inbound_rule.ports == "22-24, 80, 443"
        assert inbound_rule.protocol == "TCP"

    def test_get_public(self):
        template = self.client.load(FirewallTemplate, "public")
        assert template.slug == "public"
        self.assert_rules(template.rules)

    def test_get_vpc(self):
        template = self.client.load(FirewallTemplate, "vpc")
        assert template.slug == "vpc"
        self.assert_rules(template.rules)

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

    def test_create_device(self):
        """
        Tests that firewall devices can be created successfully
        """

        firewall = Firewall(self.client, 123)

        with self.mock_post("networking/firewalls/123/devices/123") as m:
            firewall.device_create(123, "linode")
            assert m.call_data == {"id": 123, "type": "linode"}

        with self.mock_post("networking/firewalls/123/devices/456") as m:
            firewall.device_create(123, "interface")
            assert m.call_data == {"id": 123, "type": "interface"}


class FirewallDevicesTest(ClientBaseCase):
    """
    Tests methods of Firewall devices
    """

    def test_get_devices(self):
        """
        Tests that devices can be pulled from a firewall
        """
        firewall = Firewall(self.client, 123)
        assert len(firewall.devices) == 2

        assert firewall.devices[0].created is not None
        assert firewall.devices[0].id == 123
        assert firewall.devices[0].updated is not None

        assert firewall.devices[0].entity.id == 123
        assert firewall.devices[0].entity.label == "my-linode"
        assert firewall.devices[0].entity.type == "linode"
        assert firewall.devices[0].entity.url == "/v4/linode/instances/123"

        assert firewall.devices[1].created is not None
        assert firewall.devices[1].id == 456
        assert firewall.devices[1].updated is not None

        assert firewall.devices[1].entity.id == 123
        assert firewall.devices[1].entity.label is None
        assert firewall.devices[1].entity.type == "interface"
        assert (
            firewall.devices[1].entity.url
            == "/v4/linode/instances/123/interfaces/123"
        )

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

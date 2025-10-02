from test.unit.base import ClientBaseCase

from linode_api4 import VLAN, ExplicitNullValue, Instance, Region
from linode_api4.objects import Firewall, IPAddress, IPv6Range


class NetworkingTest(ClientBaseCase):
    """
    Tests methods of the Networking class
    """

    def test_get_ipv6_range(self):
        """
        Tests that the IPv6Range object is properly generated.
        """

        ipv6Range = IPv6Range(self.client, "2600:3c01::")
        ipv6Range._api_get()

        self.assertEqual(ipv6Range.range, "2600:3c01::")
        self.assertEqual(ipv6Range.prefix, 64)
        self.assertEqual(ipv6Range.region.id, "us-east")
        self.assertEqual(ipv6Range.linodes[0], 123)
        self.assertEqual(ipv6Range.is_bgp, False)

        ranges = self.client.networking.ipv6_ranges()

        self.assertEqual(ranges[0].range, "2600:3c01::")
        self.assertEqual(ranges[0].prefix, 64)
        self.assertEqual(ranges[0].region.id, "us-east")
        self.assertEqual(
            ranges[0].route_target, "2600:3c01::ffff:ffff:ffff:ffff"
        )

    def test_get_rules(self):
        """
        Tests that you can submit a correct firewall rules view api request.
        """

        firewall = Firewall(self.client, 123)

        with self.mock_get("/networking/firewalls/123/rules") as m:
            result = firewall.get_rules()
            self.assertEqual(m.call_url, "/networking/firewalls/123/rules")
            self.assertEqual(result["inbound"], [])
            self.assertEqual(result["outbound"], [])
            self.assertEqual(result["inbound_policy"], "DROP")
            self.assertEqual(result["outbound_policy"], "DROP")

    def test_get_rule_versions(self):
        """
        Tests that you can submit a correct firewall rule versions view api request.
        """

        firewall = Firewall(self.client, 123)

        with self.mock_get("/networking/firewalls/123/history") as m:
            result = firewall.rule_versions
            self.assertEqual(m.call_url, "/networking/firewalls/123/history")
            self.assertEqual(result["data"][0]["status"], "enabled")
            self.assertEqual(result["data"][0]["rules"]["version"], 1)
            self.assertEqual(result["data"][0]["status"], "enabled")
            self.assertEqual(result["data"][1]["rules"]["version"], 2)

    def test_get_rule_version(self):
        """
        Tests that you can submit a correct firewall rule version view api request.
        """

        firewall = Firewall(self.client, 123)

        with self.mock_get("/networking/firewalls/123/history/rules/2") as m:
            result = firewall.get_rule_version(2)
            self.assertEqual(
                m.call_url, "/networking/firewalls/123/history/rules/2"
            )
            self.assertEqual(result["inbound"][0]["action"], "ACCEPT")
            self.assertEqual(
                result["inbound"][0]["addresses"]["ipv4"][0], "0.0.0.0/0"
            )
            self.assertEqual(
                result["inbound"][0]["addresses"]["ipv6"][0], "ff00::/8"
            )
            self.assertEqual(
                result["inbound"][0]["description"],
                "A really cool firewall rule.",
            )
            self.assertEqual(
                result["inbound"][0]["label"], "really-cool-firewall-rule"
            )
            self.assertEqual(result["inbound"][0]["ports"], "80")
            self.assertEqual(result["inbound"][0]["protocol"], "TCP")
            self.assertEqual(result["outbound"], [])
            self.assertEqual(result["inbound_policy"], "ACCEPT")
            self.assertEqual(result["outbound_policy"], "DROP")
            self.assertEqual(result["version"], 2)

    def test_rdns_reset(self):
        """
        Tests that the RDNS of an IP and be reset using an explicit null value.
        """

        ip = IPAddress(self.client, "127.0.0.1")

        with self.mock_put("/networking/ips/127.0.0.1") as m:
            ip.rdns = ExplicitNullValue()
            ip.save()

            self.assertEqual(m.call_url, "/networking/ips/127.0.0.1")

            # We need to assert of call_data_raw because
            # call_data drops keys with null values
            self.assertEqual(m.call_data_raw, '{"rdns": null}')

        # Ensure that everything works as expected with a class reference
        with self.mock_put("/networking/ips/127.0.0.1") as m:
            ip.rdns = ExplicitNullValue
            ip.save()

            self.assertEqual(m.call_url, "/networking/ips/127.0.0.1")

            self.assertEqual(m.call_data_raw, '{"rdns": null}')

    def test_get_ip(self):
        """
        Tests retrieving comprehensive IP address information, including all relevant properties.
        """

        ip = IPAddress(self.client, "127.0.0.1")

        def __validate_ip(_ip: IPAddress):
            assert _ip.address == "127.0.0.1"
            assert _ip.gateway == "127.0.0.1"
            assert _ip.linode_id == 123
            assert _ip.interface_id == 456
            assert _ip.prefix == 24
            assert _ip.public
            assert _ip.rdns == "test.example.org"
            assert _ip.region.id == "us-east"
            assert _ip.subnet_mask == "255.255.255.0"
            assert _ip.type == "ipv4"
            assert _ip.vpc_nat_1_1.vpc_id == 242
            assert _ip.vpc_nat_1_1.subnet_id == 194
            assert _ip.vpc_nat_1_1.address == "139.144.244.36"

        __validate_ip(ip)
        ip.invalidate()
        __validate_ip(ip)

    def test_delete_ip(self):
        """
        Tests that deleting an IP creates the correct api request
        """
        with self.mock_delete() as m:
            ip = IPAddress(self.client, "127.0.0.1")
            ip.to(Instance(self.client, 123))
            ip.delete()

            self.assertEqual(m.call_url, "/linode/instances/123/ips/127.0.0.1")

    def test_delete_vlan(self):
        """
        Tests that deleting a VLAN creates the correct api request
        """
        with self.mock_delete() as m:
            self.client.networking.delete_vlan(
                VLAN(self.client, "vlan-test"),
                Region(self.client, "us-southeast"),
            )

            self.assertEqual(
                m.call_url, "/networking/vlans/us-southeast/vlan-test"
            )

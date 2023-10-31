from test.unit.base import ClientBaseCase

from linode_api4 import ExplicitNullValue
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

    def test_vpc_nat_1_1(self):
        """
        Tests that the vpc_nat_1_1 of an IP can be retrieved.
        """

        ip = IPAddress(self.client, "127.0.0.1")

        self.assertEqual(ip.vpc_nat_1_1.vpc_id, 242)
        self.assertEqual(ip.vpc_nat_1_1.subnet_id, 194)
        self.assertEqual(ip.vpc_nat_1_1.address, "139.144.244.36")

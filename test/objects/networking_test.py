from test.base import ClientBaseCase

from linode_api4.objects import Firewall, IPAddress, IPv6Pool, IPv6Range


class NetworkingTest(ClientBaseCase):
    """
    Tests methods of the Networking class
    """

    def test_get_ipv6_pool(self):
        """
        Tests that the IPv6Pool object is properly generated.
        """

        pool = IPv6Pool(self.client, "2600:3c01::2:5000:0")

        self.assertEqual(pool.range, "2600:3c01::2:5000:0")
        self.assertEqual(pool.prefix, 124)
        self.assertEqual(pool.region.id, "us-east")
        self.assertEqual(pool.route_target, "2600:3c01::2:5000:f")

    def test_get_ipv6_range(self):
        """
        Tests that the IPv6Range object is properly generated.
        """

        ipv6Range = IPv6Range(self.client, "2600:3c01::")
        ipv6Range._api_get()

        self.assertEqual(ipv6Range.range, "2600:3c01::")
        self.assertEqual(ipv6Range.prefix, 64)
        self.assertEqual(ipv6Range.region.id, "us-east")

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

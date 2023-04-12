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

    def test_ip_addresses_share(self):
        """
        Tests that you can submit a correct ip addresses share api request.
        """

        ip = IPAddress(self.client, "192.0.2.1", {})

        with self.mock_post({}) as m:
            ip.ip_addresses_share(["192.0.2.1"], 123)
            self.assertEqual(m.call_url, "/networking/ips/share")
            self.assertEqual(m.call_data["ips"], ["192.0.2.1"])
            self.assertEqual(m.call_data["linode_id"], 123)

    def test_ip_addresses_assign(self):
        """
        Tests that you can submit a correct ip addresses assign api request.
        """

        ip = IPAddress(self.client, "192.0.2.1", {})

        with self.mock_post({}) as m:
            ip.ip_addresses_assign(
                [{"address": "192.0.2.1", "linode_id": 123}], "us-east"
            )
            self.assertEqual(m.call_url, "/networking/ips/assign")
            self.assertEqual(
                m.call_data["assignments"],
                [{"address": "192.0.2.1", "linode_id": 123}],
            )
            self.assertEqual(m.call_data["region"], "us-east")

    def test_ip_ranges_list(self):
        """
        Tests that you can submit a correct ip ranges list api request.
        """

        ipv6Range = IPv6Range(self.client, "2600:3c01::")
        ipv6Range._api_get()

        with self.mock_post("/networking/ipv6/ranges") as m:
            result = ipv6Range.ip_ranges_list()
            self.assertEqual(m.call_url, "/networking/ipv6/ranges")
            self.assertEqual(len(result), 1)

    def test_ip_range_delete(self):
        """
        Tests that you can submit a correct ip range delete api request.
        """

        ipv6Range = IPv6Range(self.client, "2600:3c01::")

        with self.mock_delete() as m:
            ipv6Range.ip_range_delete()
            self.assertEqual(m.call_url, "/networking/ipv6/ranges/2600:3c01::")

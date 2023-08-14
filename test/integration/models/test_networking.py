import pytest

from linode_api4.objects import Firewall, IPAddress, IPv6Pool, IPv6Range


@pytest.mark.smoke
def test_get_networking_rules(get_client, create_firewall):
    firewall = get_client.load(Firewall, create_firewall.id)

    rules = firewall.get_rules()

    assert "inbound" in str(rules)
    assert "inbound_policy" in str(rules)
    assert "outbound" in str(rules)
    assert "outbound_policy" in str(rules)


@pytest.mark.smoke
def test_ip_addresses_share(self):
    """
    Test that you can share IP addresses with Linode.
    """
    ip_share_url = "/networking/ips/share"
    ips = ["127.0.0.1"]
    linode_id = 12345
    with self.mock_post(ip_share_url) as m:
        result = self.client.networking.ip_addresses_share(ips, linode_id)

        self.assertIsNotNone(result)
        self.assertEqual(m.call_url, ip_share_url)
        self.assertEqual(
            m.call_data,
            {
                "ips": ips,
                "linode": linode_id,
            },
        )

    # Test that entering an empty IP array is allowed.
    with self.mock_post(ip_share_url) as m:
        result = self.client.networking.ip_addresses_share([], linode_id)

        self.assertIsNotNone(result)
        self.assertEqual(m.call_url, ip_share_url)
        self.assertEqual(
            m.call_data,
            {
                "ips": [],
                "linode": linode_id,
            },
        )

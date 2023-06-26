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

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
def test_ip_addresses_share(get_client):
    """
    Test that you can share IP addresses with Linode.
    """
    client = get_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    label = "test-ip-share"

    linode_instance, password = client.linode.instance_create(
        "g5-standard-4",
        chosen_region,
        image="linode/debian9",
        label=label,
    )

    yield linode_instance

    ips = ["127.0.0.1"]

    client.networking.ip_addresses_share(ips, linode_instance.id)

    # Test entering an empty IP to unshare.
    client.networking.ip_addresses_share([], linode_instance.id)

    linode_instance.delete()

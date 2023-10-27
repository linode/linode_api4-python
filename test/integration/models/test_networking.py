from test.integration.helpers import get_rand_nanosec_test_label

import pytest

from linode_api4.objects import Firewall


@pytest.mark.smoke
def test_get_networking_rules(test_linode_client, test_firewall):
    firewall = test_linode_client.load(Firewall, test_firewall.id)

    rules = firewall.get_rules()

    assert "inbound" in str(rules)
    assert "inbound_policy" in str(rules)
    assert "outbound" in str(rules)
    assert "outbound_policy" in str(rules)


def create_linode(get_client):
    client = get_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    label = get_rand_nanosec_test_label()

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1",
        chosen_region,
        image="linode/debian12",
        label=label,
    )

    return linode_instance


@pytest.fixture
def create_linode_for_ip_share(get_client):
    linode = create_linode(get_client)

    yield linode

    linode.delete()


@pytest.fixture
def create_linode_to_be_shared_with_ips(get_client):
    linode = create_linode(get_client)

    yield linode

    linode.delete()


@pytest.mark.smoke
def test_ip_addresses_share(
    get_client, create_linode_for_ip_share, create_linode_to_be_shared_with_ips
):
    """
    Test that you can share IP addresses with Linode.
    """

    # create two linode instances and share the ip of instance1 with instance2
    linode_instance1 = create_linode_for_ip_share
    linode_instance2 = create_linode_to_be_shared_with_ips

    get_client.networking.ip_addresses_share(
        [linode_instance1.ips.ipv4.public[0]], linode_instance2.id
    )

    assert (
        linode_instance1.ips.ipv4.public[0].address
        == linode_instance2.ips.ipv4.shared[0].address
    )


@pytest.mark.smoke
def test_ip_addresses_unshare(
    get_client, create_linode_for_ip_share, create_linode_to_be_shared_with_ips
):
    """
    Test that you can unshare IP addresses with Linode.
    """

    # create two linode instances and share the ip of instance1 with instance2
    linode_instance1 = create_linode_for_ip_share
    linode_instance2 = create_linode_to_be_shared_with_ips

    get_client.networking.ip_addresses_share(
        [linode_instance1.ips.ipv4.public[0]], linode_instance2.id
    )

    # unshared the ip with instance2
    get_client.networking.ip_addresses_share([], linode_instance2.id)

    assert [] == linode_instance2.ips.ipv4.shared

from test.integration.helpers import get_rand_nanosec_test_label

import pytest

from linode_api4.objects import Config, ConfigInterfaceIPv4, Firewall, IPAddress


@pytest.mark.smoke
def test_get_networking_rules(test_linode_client, test_firewall):
    firewall = test_linode_client.load(Firewall, test_firewall.id)

    rules = firewall.get_rules()

    assert "inbound" in str(rules)
    assert "inbound_policy" in str(rules)
    assert "outbound" in str(rules)
    assert "outbound_policy" in str(rules)


def create_linode(test_linode_client):
    client = test_linode_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    label = get_rand_nanosec_test_label()

    linode_instance, _ = client.linode.instance_create(
        "g6-nanode-1",
        chosen_region,
        image="linode/debian12",
        label=label,
    )

    return linode_instance


@pytest.fixture
def create_linode_for_ip_share(test_linode_client):
    linode = create_linode(test_linode_client)

    yield linode

    linode.delete()


@pytest.fixture
def create_linode_to_be_shared_with_ips(test_linode_client):
    linode = create_linode(test_linode_client)

    yield linode

    linode.delete()


@pytest.mark.smoke
def test_ip_addresses_share(
    test_linode_client,
    create_linode_for_ip_share,
    create_linode_to_be_shared_with_ips,
):
    """
    Test that you can share IP addresses with Linode.
    """

    # create two linode instances and share the ip of instance1 with instance2
    linode_instance1 = create_linode_for_ip_share
    linode_instance2 = create_linode_to_be_shared_with_ips

    test_linode_client.networking.ip_addresses_share(
        [linode_instance1.ips.ipv4.public[0]], linode_instance2.id
    )

    assert (
        linode_instance1.ips.ipv4.public[0].address
        == linode_instance2.ips.ipv4.shared[0].address
    )


@pytest.mark.smoke
def test_ip_addresses_unshare(
    test_linode_client,
    create_linode_for_ip_share,
    create_linode_to_be_shared_with_ips,
):
    """
    Test that you can unshare IP addresses with Linode.
    """

    # create two linode instances and share the ip of instance1 with instance2
    linode_instance1 = create_linode_for_ip_share
    linode_instance2 = create_linode_to_be_shared_with_ips

    test_linode_client.networking.ip_addresses_share(
        [linode_instance1.ips.ipv4.public[0]], linode_instance2.id
    )

    # unshared the ip with instance2
    test_linode_client.networking.ip_addresses_share([], linode_instance2.id)

    assert [] == linode_instance2.ips.ipv4.shared


def test_ip_info_vpc(test_linode_client, create_vpc_with_subnet_and_linode):
    vpc, subnet, linode, _ = create_vpc_with_subnet_and_linode

    config: Config = linode.configs[0]

    config.interfaces = []
    config.save()

    _ = config.interface_create_vpc(
        subnet=subnet,
        primary=True,
        ipv4=ConfigInterfaceIPv4(vpc="10.0.0.2", nat_1_1="any"),
        ip_ranges=["10.0.0.5/32"],
    )

    config.invalidate()

    ip_info = test_linode_client.load(IPAddress, linode.ipv4[0])

    assert ip_info.vpc_nat_1_1.address == "10.0.0.2"
    assert ip_info.vpc_nat_1_1.vpc_id == vpc.id
    assert ip_info.vpc_nat_1_1.subnet_id == subnet.id

import copy
import ipaddress

import pytest

from linode_api4 import (
    ApiError,
    Instance,
    LinodeInterface,
    LinodeInterfaceDefaultRouteOptions,
    LinodeInterfacePublicIPv4AddressOptions,
    LinodeInterfacePublicIPv4Options,
    LinodeInterfacePublicIPv6Options,
    LinodeInterfacePublicIPv6RangeOptions,
    LinodeInterfacePublicOptions,
    LinodeInterfaceVLANOptions,
    LinodeInterfaceVPCIPv4AddressOptions,
    LinodeInterfaceVPCIPv4Options,
    LinodeInterfaceVPCIPv4RangeOptions,
    LinodeInterfaceVPCOptions,
)


def test_linode_create_with_linode_interfaces(
    create_vpc_with_subnet,
    linode_with_linode_interfaces,
):
    instance: Instance = linode_with_linode_interfaces
    vpc, subnet = create_vpc_with_subnet

    def __assert_base(iface: LinodeInterface):
        assert iface.id is not None
        assert iface.linode_id == instance.id

        assert iface.created is not None
        assert iface.updated is not None

        assert isinstance(iface.mac_address, str)
        assert iface.version

    def __assert_public(iface: LinodeInterface):
        __assert_base(iface)

        assert iface.default_route.ipv4
        assert iface.default_route.ipv6

        assert iface.public.ipv4.addresses[0].address == instance.ipv4[0]
        assert iface.public.ipv4.addresses[0].primary
        assert len(iface.public.ipv4.shared) == 0

        assert iface.public.ipv6.slaac[0].address == instance.ipv6.split("/")[0]
        assert iface.public.ipv6.slaac[0].prefix == 64
        assert len(iface.public.ipv6.shared) == 0
        assert len(iface.public.ipv6.ranges) == 0

    def __assert_vpc(iface: LinodeInterface):
        __assert_base(iface)

        assert not iface.default_route.ipv4
        assert not iface.default_route.ipv6

        assert iface.vpc.vpc_id == vpc.id
        assert iface.vpc.subnet_id == subnet.id

        assert ipaddress.ip_address(
            iface.vpc.ipv4.addresses[0].address
        ) in ipaddress.ip_network(subnet.ipv4)
        assert iface.vpc.ipv4.addresses[0].primary
        assert iface.vpc.ipv4.addresses[0].nat_1_1_address is None

        assert len(iface.vpc.ipv4.ranges) == 0

    def __assert_vlan(iface: LinodeInterface):
        __assert_base(iface)

        assert not iface.default_route.ipv4
        assert not iface.default_route.ipv6

        assert iface.vlan.vlan_label == "test-vlan"
        assert iface.vlan.ipam_address == "10.0.0.5/32"

    __assert_public(instance.linode_interfaces[0])
    __assert_vpc(instance.linode_interfaces[1])
    __assert_vlan(instance.linode_interfaces[2])

    instance.invalidate()

    __assert_public(instance.linode_interfaces[0])
    __assert_vpc(instance.linode_interfaces[1])
    __assert_vlan(instance.linode_interfaces[2])


@pytest.fixture
def linode_interface_public(
    test_linode_client,
    e2e_test_firewall,
    linode_with_interface_generation_linode,
):
    instance: Instance = linode_with_interface_generation_linode

    ipv6_range = test_linode_client.networking.ipv6_range_allocate(
        64, linode=instance.id
    )

    yield instance.interface_create(
        firewall_id=e2e_test_firewall.id,
        default_route=LinodeInterfaceDefaultRouteOptions(
            ipv4=True,
            ipv6=True,
        ),
        public=LinodeInterfacePublicOptions(
            ipv4=LinodeInterfacePublicIPv4Options(
                addresses=[
                    LinodeInterfacePublicIPv4AddressOptions(
                        address=instance.ips.ipv4.public[0].address,
                        primary=True,
                    )
                ]
            ),
            ipv6=LinodeInterfacePublicIPv6Options(
                ranges=[
                    LinodeInterfacePublicIPv6RangeOptions(
                        range=ipv6_range.range,
                    )
                ]
            ),
        ),
    ), instance, ipv6_range


@pytest.fixture
def linode_interface_vpc(
    test_linode_client,
    e2e_test_firewall,
    linode_with_interface_generation_linode,
    create_vpc_with_subnet,
):
    instance: Instance = linode_with_interface_generation_linode
    vpc, subnet = create_vpc_with_subnet

    yield instance.interface_create(
        firewall_id=e2e_test_firewall.id,
        default_route=LinodeInterfaceDefaultRouteOptions(
            ipv4=True,
        ),
        vpc=LinodeInterfaceVPCOptions(
            subnet_id=subnet.id,
            ipv4=LinodeInterfaceVPCIPv4Options(
                addresses=[
                    LinodeInterfaceVPCIPv4AddressOptions(
                        address="auto",
                        primary=True,
                        nat_1_1_address="auto",
                    )
                ],
                ranges=[
                    LinodeInterfaceVPCIPv4RangeOptions(
                        range="/32",
                    )
                ],
            ),
        ),
    ), instance, vpc, subnet


@pytest.fixture
def linode_interface_vlan(
    test_linode_client,
    e2e_test_firewall,
    linode_with_interface_generation_linode,
    create_vpc_with_subnet,
):
    instance: Instance = linode_with_interface_generation_linode

    yield instance.interface_create(
        vlan=LinodeInterfaceVLANOptions(
            vlan_label="test-vlan", ipam_address="10.0.0.5/32"
        ),
    ), instance


def test_linode_interface_create_public(linode_interface_public):
    iface, instance, ipv6_range = linode_interface_public

    assert iface.id is not None
    assert iface.linode_id == instance.id

    assert iface.created is not None
    assert iface.updated is not None

    assert isinstance(iface.mac_address, str)
    assert iface.version

    assert iface.default_route.ipv4
    assert iface.default_route.ipv6

    assert (
        iface.public.ipv4.addresses[0].address
        == instance.ips.ipv4.public[0].address
    )
    assert iface.public.ipv4.addresses[0].primary
    assert len(iface.public.ipv4.shared) == 0

    assert iface.public.ipv6.ranges[0].range == ipv6_range.range
    assert (
        iface.public.ipv6.ranges[0].route_target == instance.ipv6.split("/")[0]
    )
    assert iface.public.ipv6.slaac[0].address == instance.ipv6.split("/")[0]
    assert iface.public.ipv6.slaac[0].prefix == 64
    assert len(iface.public.ipv6.shared) == 0


def test_linode_interface_update_public(linode_interface_public):
    iface, instance, ipv6_range = linode_interface_public

    old_public_ipv4 = copy.deepcopy(iface.public.ipv4)

    iface.public.ipv4.addresses += [
        LinodeInterfacePublicIPv4AddressOptions(address="auto", primary=True)
    ]
    iface.public.ipv4.addresses[0].primary = False

    iface.public.ipv6.ranges[0].range = "/64"

    iface.save()

    iface.invalidate()

    assert len(iface.public.ipv4.addresses) == 2

    address = iface.public.ipv4.addresses[0]
    assert address.address == old_public_ipv4.addresses[0].address
    assert not address.primary

    address = iface.public.ipv4.addresses[1]
    assert ipaddress.ip_address(address.address)
    assert address.primary

    assert len(iface.public.ipv6.ranges) == 1

    range = iface.public.ipv6.ranges[0]
    assert len(range.range) > 0
    assert ipaddress.ip_network(range.range)


def test_linode_interface_create_vpc(linode_interface_vpc):
    iface, instance, vpc, subnet = linode_interface_vpc

    assert iface.id is not None
    assert iface.linode_id == instance.id

    assert iface.created is not None
    assert iface.updated is not None

    assert isinstance(iface.mac_address, str)
    assert iface.version

    assert iface.default_route.ipv4
    assert not iface.default_route.ipv6

    assert iface.vpc.vpc_id == vpc.id
    assert iface.vpc.subnet_id == subnet.id

    assert len(iface.vpc.ipv4.addresses[0].address) > 0
    assert iface.vpc.ipv4.addresses[0].primary
    assert iface.vpc.ipv4.addresses[0].nat_1_1_address is not None

    assert iface.vpc.ipv4.ranges[0].range.split("/")[1] == "32"


def test_linode_interface_update_vpc(linode_interface_vpc):
    iface, instance, vpc, subnet = linode_interface_vpc

    iface.vpc.subnet_id = 0

    try:
        iface.save()
    except ApiError:
        pass
    else:
        raise Exception("Expected error when updating subnet_id to 0")

    iface.invalidate()

    old_ipv4 = copy.deepcopy(iface.vpc.ipv4)

    iface.vpc.ipv4.addresses[0].address = "auto"
    iface.vpc.ipv4.ranges += [
        LinodeInterfaceVPCIPv4RangeOptions(
            range="/32",
        )
    ]

    iface.save()
    iface.invalidate()

    address = iface.vpc.ipv4.addresses[0]
    assert ipaddress.ip_address(address.address)

    range = iface.vpc.ipv4.ranges[0]
    assert ipaddress.ip_network(range.range)
    assert range.range == old_ipv4.ranges[0].range

    range = iface.vpc.ipv4.ranges[1]
    assert ipaddress.ip_network(range.range)
    assert range.range != old_ipv4.ranges[0].range


def test_linode_interface_create_vlan(
    linode_interface_vlan,
):
    iface, instance = linode_interface_vlan

    assert iface.id is not None
    assert iface.linode_id == instance.id

    assert iface.created is not None
    assert iface.updated is not None

    assert isinstance(iface.mac_address, str)
    assert iface.version

    assert not iface.default_route.ipv4
    assert not iface.default_route.ipv6

    assert iface.vlan.vlan_label == "test-vlan"
    assert iface.vlan.ipam_address == "10.0.0.5/32"


# NOTE: VLAN interface updates current aren't supported


def test_linode_interface_firewalls(e2e_test_firewall, linode_interface_public):
    iface, instance, ipv6_range = linode_interface_public

    assert iface.id is not None
    assert iface.linode_id == instance.id

    firewalls = iface.firewalls()

    firewall = firewalls[0]
    assert firewall.id == e2e_test_firewall.id
    assert firewall.label == e2e_test_firewall.label

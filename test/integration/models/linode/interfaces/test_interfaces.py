import copy
import ipaddress
import os
from test.integration.helpers import get_test_label, wait_for_condition

import pytest

from linode_api4 import (
    ApiError,
    Instance,
    InterfaceGeneration,
    LinodeInterface,
    LinodeInterfaceDefaultRouteOptions,
    LinodeInterfaceOptions,
    LinodeInterfacePublicIPv4AddressOptions,
    LinodeInterfacePublicIPv4Options,
    LinodeInterfacePublicIPv6Options,
    LinodeInterfacePublicIPv6RangeOptions,
    LinodeInterfacePublicOptions,
    LinodeInterfaceRDMAVPCIPv4AddressOptions,
    LinodeInterfaceRDMAVPCIPv4Options,
    LinodeInterfaceRDMAVPCOptions,
    LinodeInterfaceVLANOptions,
    LinodeInterfaceVPCIPv4AddressOptions,
    LinodeInterfaceVPCIPv4Options,
    LinodeInterfaceVPCIPv4RangeOptions,
    LinodeInterfaceVPCOptions,
    ReservedIPAddress,
)


def build_interface_public_ipv4(firewall, ip_address):
    return LinodeInterfaceOptions(
        firewall_id=firewall,
        default_route=LinodeInterfaceDefaultRouteOptions(
            ipv4=True,
        ),
        public=LinodeInterfacePublicOptions(
            ipv4=LinodeInterfacePublicIPv4Options(
                addresses=[
                    LinodeInterfacePublicIPv4AddressOptions(
                        address=ip_address, primary=True
                    )
                ],
            ),
        ),
    )


def build_interface_rdma_vpc_ipv4(subnet_id: int):
    return LinodeInterfaceOptions(
        firewall_id=-1,
        rdma_vpc=LinodeInterfaceRDMAVPCOptions(
            subnet_id=subnet_id,
            ipv4=LinodeInterfaceRDMAVPCIPv4Options(
                addresses=[
                    LinodeInterfaceRDMAVPCIPv4AddressOptions(
                        address="auto", primary=True
                    )
                ]
            ),
        ),
    )


def create_linode_with_legacy_config(
    client, ip_address, label, firewall, authorized_key
):
    linode = client.linode.instance_create(
        "g6-nanode-1",
        ip_address.region,
        image="linode/debian12",
        label=label,
        firewall=firewall,
        interface_generation=InterfaceGeneration.LEGACY_CONFIG,
        authorized_keys=authorized_key,
        ipv4=[ip_address.address],
    )
    return linode


def create_linode_with_standard_interfaces(
    client, ip_address, label, firewall, authorized_key
):
    interface = build_interface_public_ipv4(firewall.id, ip_address.address)
    linode = client.linode.instance_create(
        "g6-nanode-1",
        ip_address.region,
        image="linode/debian12",
        label=label,
        interface_generation=InterfaceGeneration.LINODE,
        authorized_keys=authorized_key,
        interfaces=[interface],
    )
    return linode


def create_multiple_rdma_interfaces(amount: int, subnet_id: int):
    """
    Creates multiple VPC RDMA interfaces that may be needed for RDMA Linode instance

    Note:
    At least 8 separate VPC RDMA interfaces need to be created for a single RDMA linode instance
    """
    interfaces = list()

    for _ in range(amount):
        rdma_iface = build_interface_rdma_vpc_ipv4(subnet_id)
        interfaces.append(rdma_iface)

    return interfaces


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

        slaac_entry = iface.vpc.ipv6.slaac[0]
        assert ipaddress.ip_address(
            slaac_entry.address
        ) in ipaddress.ip_network(slaac_entry.range)
        assert not iface.vpc.ipv6.is_public
        assert len(iface.vpc.ipv6.ranges) == 0

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
                        nat_1_1_address=None,
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
    assert iface.default_route.ipv6

    assert iface.vpc.vpc_id == vpc.id
    assert iface.vpc.subnet_id == subnet.id

    assert len(iface.vpc.ipv4.addresses[0].address) > 0
    assert iface.vpc.ipv4.addresses[0].primary

    assert iface.vpc.ipv4.addresses[0].nat_1_1_address is None

    assert iface.vpc.ipv4.ranges[0].range.split("/")[1] == "32"

    assert iface.default_route.ipv6
    ipv6 = iface.vpc.ipv6
    assert ipv6 and ipv6.is_public is False

    if ipv6.slaac:
        assert ipv6.ranges == [] and len(ipv6.slaac) == 1
        assert ipv6.slaac[0].range and ipv6.slaac[0].address
    elif ipv6.ranges:
        assert ipv6.slaac == [] and len(ipv6.ranges) > 0


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


@pytest.mark.parametrize(
    "create_linode_fn",
    [create_linode_with_legacy_config, create_linode_with_standard_interfaces],
    ids=["legacy_config", "standard_interfaces"],
)
def test_linode_interfaces_with_reserved_ips(
    test_linode_client,
    e2e_test_firewall,
    create_reserved_ip,
    create_linode_fn,
    ssh_key_gen,
):
    client = test_linode_client
    reserved_ip = create_reserved_ip
    label = get_test_label(length=8)

    linode = create_linode_fn(
        client, reserved_ip, label, e2e_test_firewall, ssh_key_gen[0]
    )

    try:
        linode_ips = linode.ips.ipv4.public
        assert len(linode_ips) == 1
        assert linode_ips[0].address == reserved_ip.address
        assert linode_ips[0].reserved == True
        assert linode_ips[0].linode_id == linode.id
        assert linode_ips[0].assigned_entity.id == linode.id
        assert linode_ips[0].assigned_entity.type == "linode"
        assert linode_ips[0].assigned_entity.label == linode.label
        assert (
            linode_ips[0].assigned_entity.url
            == f"/v4/linode/instances/{linode.id}"
        )
    finally:
        linode.delete()

    reserved_ips_list = client.networking.reserved_ips(
        ReservedIPAddress.address == reserved_ip.address
    )
    assert len(reserved_ips_list) == 1
    assert reserved_ips_list[0].reserved == True
    assert reserved_ips_list[0].linode_id is None
    assert reserved_ips_list[0].assigned_entity is None


@pytest.mark.skipif(
    os.getenv("RUN_RDMA_TESTS", "").strip().lower() not in {"yes", "true"},
    reason="Linode with RDMA interfaces requires manual infra changes; set RUN_RDMA_TESTS=yes to enable",
)
def test_linode_interfaces_with_rdma_vpc_type(
    request,
    test_linode_client,
):
    client = test_linode_client
    region = "us-rno-1"

    # Create a regular VPC with a subnet in us-rno-1
    vpc = client.vpcs.create(
        label=get_test_label(length=10),
        region=region,
        description="test description",
        ipv6=[{"range": "auto"}],
    )
    request.addfinalizer(vpc.delete)
    subnet = vpc.subnet_create(
        label="test-subnet",
        ipv4="10.0.0.0/24",
        ipv6=[{"range": "auto"}],
    )
    request.addfinalizer(subnet.delete)

    # Create an RDMA VPC with a subnet in us-rno-1
    vpc_rdma = client.vpcs.create(
        label=get_test_label(length=10),
        region=region,
        description="test description",
        vpc_type="rdma",
    )
    request.addfinalizer(vpc_rdma.delete)
    subnet_rdma = vpc_rdma.subnet_create(
        label=get_test_label(length=10),
        ipv4="10.0.0.0/24",
    )
    request.addfinalizer(subnet_rdma.delete)

    # Include RDMA VPC interfaces
    multi_ifaces = create_multiple_rdma_interfaces(8, subnet_rdma.id)

    # Include (at least one) regular interface
    multi_ifaces.append(
        LinodeInterfaceOptions(
            firewall_id=-1,
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
                        )
                    ],
                ),
            ),
        ),
    )

    instance = client.linode.instance_create(
        label="python-test-rdma-" + get_test_label(),
        root_pass="aComplex@Password123",
        image="linode/ubuntu24.04",
        region=vpc.region,
        ltype="g3-gpu-rtxpro6000-blackwell-rdma-8",
        interface_generation=InterfaceGeneration.LINODE,
        interfaces=multi_ifaces,
        booted=False,
    )
    request.addfinalizer(instance.delete)

    def get_linode_status():
        instance.invalidate()
        return instance.status == "offline"

    wait_for_condition(5, 180, get_linode_status)

    assert len(instance.linode_interfaces) == len(multi_ifaces)

import ipaddress
import time
from test.integration.conftest import (
    get_api_ca_file,
    get_api_url,
    get_region,
    get_token,
)
from test.integration.helpers import (
    get_test_label,
    retry_sending_request,
    wait_for_condition,
)

import pytest
import requests

from linode_api4 import (
    ApiError,
    Capability,
    Instance,
    InterfaceGeneration,
    LinodeClient,
)
from linode_api4.objects import (
    Config,
    ConfigInterfaceIPv4,
    Firewall,
    IPAddress,
    LinodeInterfaceDefaultRouteOptions,
    LinodeInterfaceVPCIPv4AddressOptions,
    LinodeInterfaceVPCIPv4Options,
    LinodeInterfaceVPCIPv4RangeOptions,
    LinodeInterfaceVPCOptions,
    NATGateway,
    ReservedIPAddress,
    VPCSubnetNATGatewayOptions,
)
from linode_api4.objects.networking import (
    FirewallCreateDevicesOptions,
    NetworkTransferPrice,
    Price,
)

TEST_REGION = get_region(
    LinodeClient(
        token=get_token(),
        base_url=get_api_url(),
        ca_path=get_api_ca_file(),
    ),
    {Capability.linodes, Capability.firewall},
    site_type="core",
)


def create_linode_func(test_linode_client):
    client = test_linode_client

    label = get_test_label()

    linode_instance = client.linode.instance_create(
        "g6-nanode-1",
        TEST_REGION,
        image="linode/debian12",
        label=label,
        root_pass="aComplex@Password123",
    )

    return linode_instance


@pytest.fixture
def create_linode_for_ip_share(test_linode_client):
    linode = create_linode_func(test_linode_client)

    yield linode

    linode.delete()


@pytest.fixture
def create_linode_to_be_shared_with_ips(test_linode_client):
    linode = create_linode_func(test_linode_client)

    yield linode

    linode.delete()


@pytest.mark.smoke
def test_get_networking_rules(test_linode_client, test_firewall):
    firewall = test_linode_client.load(Firewall, test_firewall.id)

    rules = firewall.get_rules()

    assert "inbound" in str(rules)
    assert "inbound_policy" in str(rules)
    assert "outbound" in str(rules)
    assert "outbound_policy" in str(rules)


@pytest.fixture
def create_linode_without_firewall(test_linode_client):
    """
    WARNING: This is specifically reserved for Firewall testing.
             Don't use this if the Linode will not be assigned to a firewall.
    """

    client = test_linode_client
    region = get_region(client, {"Cloud Firewall"}, "core").id

    label = get_test_label()

    instance = client.linode.instance_create(
        "g6-nanode-1",
        region,
        label=label,
    )

    yield client, instance

    instance.delete()


@pytest.fixture
def create_firewall_with_device(create_linode_without_firewall):
    client, target_instance = create_linode_without_firewall

    firewall = client.networking.firewall_create(
        get_test_label(),
        rules={
            "inbound_policy": "DROP",
            "outbound_policy": "DROP",
        },
        devices=FirewallCreateDevicesOptions(linodes=[target_instance.id]),
    )

    yield firewall, target_instance

    firewall.delete()


@pytest.fixture
def create_nat_vpc_with_subnet(test_linode_client, create_nat_vpc):
    subnet = create_nat_vpc.subnet_create(
        label="test-nat-subnet",
        ipv4="10.0.0.0/24",
        ipv6=[{"range": "auto"}],
    )

    yield create_nat_vpc, subnet

    subnet.delete()


@pytest.fixture
def create_nat_vpc_with_subnet_and_linode(
    test_linode_client, create_nat_vpc_with_subnet, e2e_test_firewall
):
    vpc, subnet = create_nat_vpc_with_subnet

    instance = test_linode_client.linode.instance_create(
        "g6-standard-1",
        vpc.region,
        label=get_test_label(length=8),
        firewall=e2e_test_firewall,
        interface_generation=InterfaceGeneration.LINODE,
        booted=False,
    )

    yield vpc, subnet, instance

    instance.delete()


def test_get_networking_rule_versions(test_linode_client, test_firewall):
    firewall = test_linode_client.load(Firewall, test_firewall.id)

    # Update the firewall's rules
    new_rules = {
        "inbound": [
            {
                "action": "ACCEPT",
                "addresses": {
                    "ipv4": ["0.0.0.0/0"],
                    "ipv6": ["ff00::/8"],
                },
                "description": "A really cool firewall rule.",
                "label": "really-cool-firewall-rule",
                "ports": "80",
                "protocol": "TCP",
            }
        ],
        "inbound_policy": "ACCEPT",
        "outbound": [],
        "outbound_policy": "DROP",
    }
    firewall.update_rules(new_rules)
    time.sleep(1)

    rule_versions = firewall.rule_versions

    # Original firewall rules
    old_rule_version = firewall.get_rule_version(1)

    # Updated firewall rules
    new_rule_version = firewall.get_rule_version(2)

    assert "rules" in str(rule_versions)
    assert "version" in str(rule_versions)
    assert rule_versions["results"] == 2

    assert old_rule_version["inbound"] == []
    assert old_rule_version["inbound_policy"] == "ACCEPT"
    assert old_rule_version["outbound"] == []
    assert old_rule_version["outbound_policy"] == "DROP"
    assert old_rule_version["version"] == 1

    assert (
        new_rule_version["inbound"][0]["description"]
        == "A really cool firewall rule."
    )
    assert new_rule_version["inbound_policy"] == "ACCEPT"
    assert new_rule_version["outbound"] == []
    assert new_rule_version["outbound_policy"] == "DROP"
    assert new_rule_version["version"] == 2


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
    vpc, subnet, linode = create_vpc_with_subnet_and_linode

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


def test_network_transfer_prices(test_linode_client):
    transfer_prices = test_linode_client.networking.transfer_prices()

    if len(transfer_prices) > 0:
        assert type(transfer_prices[0]) is NetworkTransferPrice
        assert type(transfer_prices[0].price) is Price
        assert (
            transfer_prices[0].price is None
            or transfer_prices[0].price.hourly >= 0
        )


def test_allocate_and_delete_ip(test_linode_client, create_linode):
    linode = create_linode
    ip = test_linode_client.networking.ip_allocate(linode.id)
    linode.invalidate()

    assert ip.linode_id == linode.id
    assert ip.address in linode.ipv4

    is_deleted = ip.delete()

    assert is_deleted is True


def get_status(linode: Instance, status: str):
    return linode.status == status


def test_create_and_delete_vlan(test_linode_client, linode_for_vlan_tests):
    linode = linode_for_vlan_tests

    config: Config = linode.configs[0]

    config.interfaces = []
    config.save()

    vlan_label = f"{get_test_label(8)}-testvlan"
    interface = config.interface_create_vlan(
        label=vlan_label, ipam_address="10.0.0.2/32"
    )

    config.invalidate()

    assert interface.id == config.interfaces[0].id
    assert interface.purpose == "vlan"
    assert interface.label == vlan_label

    # Remove the VLAN interface and reboot Linode
    config.interfaces = []
    config.save()

    wait_for_condition(3, 150, get_status, linode, "running")

    retry_sending_request(3, linode.reboot)

    wait_for_condition(3, 100, get_status, linode, "rebooting")
    assert linode.status == "rebooting"

    wait_for_condition(3, 150, get_status, linode, "running")

    # Delete the VLAN
    is_deleted = test_linode_client.networking.delete_vlan(
        vlan_label, linode.region
    )

    assert is_deleted is True


def test_create_firewall_with_linode_device(create_firewall_with_device):
    firewall, target_instance = create_firewall_with_device

    devices = firewall.devices

    assert len(devices) == 1
    assert devices[0].entity.id == target_instance.id


# TODO (Enhanced Interfaces): Add test for interface device


def test_get_global_firewall_settings(test_linode_client):
    settings = test_linode_client.networking.firewall_settings()

    assert settings.default_firewall_ids is not None
    assert all(
        k in {"vpc_interface", "public_interface", "linode", "nodebalancer"}
        for k in vars(settings.default_firewall_ids).keys()
    )


def test_ip_info(test_linode_client, create_linode):
    linode = create_linode
    wait_for_condition(3, 100, get_status, linode, "running")

    ip_info = test_linode_client.load(IPAddress, linode.ipv4[0])

    assert ip_info.address == linode.ipv4[0]
    assert ip_info.gateway is not None
    assert ip_info.linode_id == linode.id
    assert ip_info.interface_id is None
    assert ip_info.prefix == 24
    assert ip_info.public
    assert ip_info.rdns is not None
    assert ip_info.region.id == linode.region.id
    assert ip_info.subnet_mask is not None
    assert ip_info.type == "ipv4"
    assert ip_info.vpc_nat_1_1 is None


def verify_reserved_ip(reserved_ip):
    assert isinstance(
        ipaddress.ip_address(reserved_ip.address), ipaddress.IPv4Address
    )
    assert reserved_ip.type == "ipv4"
    assert reserved_ip.public == True
    assert reserved_ip.reserved == True
    assert reserved_ip.linode_id is None
    assert reserved_ip.assigned_entity is None


def verify_reserved_ip_assigned(reserved_ip, resource):
    assert isinstance(
        ipaddress.ip_address(reserved_ip.address), ipaddress.IPv4Address
    )
    assert reserved_ip.type == "ipv4"
    assert reserved_ip.public == True
    assert reserved_ip.reserved == True
    assert reserved_ip.linode_id == resource.id
    assert reserved_ip.region.id == resource.region.id
    assert reserved_ip.assigned_entity.id == resource.id
    assert reserved_ip.assigned_entity.type == "linode"
    assert reserved_ip.assigned_entity.label == resource.label
    assert (
        reserved_ip.assigned_entity.url == f"/v4/linode/instances/{resource.id}"
    )


@pytest.mark.smoke
@pytest.mark.parametrize(
    "region, tags, expected",
    [
        (TEST_REGION, ["test"], ["test"]),
        (TEST_REGION, None, []),
    ],
)
def test_create_reserved_ip(
    request, test_linode_client, region, tags, expected
):
    client = test_linode_client
    reserved_ip = client.networking.reserved_ip_create(region=region, tags=tags)
    request.addfinalizer(reserved_ip.delete)

    verify_reserved_ip(reserved_ip)
    assert reserved_ip.tags == expected


def test_create_reserved_ip_wo_region_fail(test_linode_client):
    client = test_linode_client

    with pytest.raises(ApiError) as exc_info:
        client.networking.reserved_ip_create(region=None, tags=["test"])

    error_msg = str(exc_info.value.json)
    assert exc_info.value.status == 400
    assert "region is required" in error_msg


def test_update_reserved_ip_tags(test_linode_client, create_reserved_ip):
    client = test_linode_client
    reserved_ip = create_reserved_ip
    verify_reserved_ip(reserved_ip)
    assert reserved_ip.tags == ["test"]

    reserved_ip.tags = ["updated"]
    reserved_ip.save()
    reserved_ip = client.networking.reserved_ips(
        ReservedIPAddress.address == reserved_ip.address
    )[0]
    verify_reserved_ip(reserved_ip)
    assert reserved_ip.tags == ["updated"]


def test_create_reserved_ip_assigned(
    test_linode_client, create_reserved_ip_assigned
):
    client = test_linode_client
    linode, reserved_ip = create_reserved_ip_assigned
    verify_reserved_ip_assigned(reserved_ip, linode)
    assert sorted(reserved_ip.tags) == ["assigned", "test"]

    reserved_ips_list = client.networking.reserved_ips()
    assert reserved_ip.address in [ip.address for ip in reserved_ips_list]

    linode_ips = linode.ips.ipv4.public
    assert len(linode_ips) == 2
    assert any([ip.reserved for ip in linode_ips])

    reserved_ip.delete()
    reserved_ips_list = client.networking.reserved_ips()
    assert reserved_ip.address not in [ip.address for ip in reserved_ips_list]

    reserved_ips_list = client.networking.reserved_ips(
        ReservedIPAddress.address == reserved_ip.address
    )
    assert len(reserved_ips_list) == 0

    delattr(linode, "_ips")
    linode_ips = linode.ips.ipv4.public
    assert len(linode_ips) == 2
    assert not any([ip.reserved for ip in linode_ips])
    assert not any([ip.tags for ip in linode_ips])  # Tags should be removed


def test_get_reserved_ip_types(test_linode_client):
    client = test_linode_client
    endpoint = client.base_url + "/networking/reserved/ips/types"
    types = requests.get(endpoint).json()[
        "data"
    ]  # Pricing should be publicly available

    assert isinstance(types, list)
    assert types[0]["id"] == "reserved-ipv4"
    assert types[0]["label"] == "Reserved IPv4"
    assert "hourly" in types[0]["price"]
    assert "monthly" in types[0]["price"]
    assert any(price != 0 for price in list(types[0]["price"].values()))
    assert isinstance(types[0]["region_prices"], list)


@pytest.mark.smoke
def test_create_reserved_ip_with_allocate_and_region(test_linode_client):
    client = test_linode_client
    reserved_ip = client.networking.ip_allocate(
        reserved=True, region=TEST_REGION
    )

    verify_reserved_ip(reserved_ip)
    assert reserved_ip.tags == []

    # clean-up
    reserved_ip = client.load(ReservedIPAddress, reserved_ip.address)
    reserved_ip.delete()


@pytest.mark.smoke
def test_create_reserved_ip_with_allocate_and_linode(
    test_linode_client, create_linode
):
    client = test_linode_client
    linode = create_linode
    reserved_ip = client.networking.ip_allocate(reserved=True, linode=linode.id)

    verify_reserved_ip_assigned(reserved_ip, linode)
    assert reserved_ip.tags == []

    # clean-up
    reserved_ip = client.load(ReservedIPAddress, reserved_ip.address)
    reserved_ip.delete()

    # Delete assigned IP address completely
    if address := client.networking.ips(
        IPAddress.address == reserved_ip.address
    ):
        address[0].delete()


def test_reserve_ephemeral_ip(test_linode_client, create_linode):
    client = test_linode_client
    linode = create_linode

    ip_address = client.load(IPAddress, linode.ipv4[0])
    assert ip_address.linode_id == linode.id
    assert ip_address.reserved == False

    ip_address.reserved = True
    ip_address.save()
    ip_address = client.load(IPAddress, linode.ipv4[0])
    assert ip_address.linode_id == linode.id
    assert ip_address.reserved == True

    ip_address.reserved = False
    ip_address.save()
    ip_address = client.load(IPAddress, linode.ipv4[0])
    assert ip_address.linode_id == linode.id
    assert ip_address.reserved == False


def test_convert_unassigned_reserved_ip_to_ephemeral(
    test_linode_client, create_reserved_ip
):
    client = test_linode_client
    reserved_ip = create_reserved_ip
    verify_reserved_ip(reserved_ip)

    ip_address = client.load(IPAddress, reserved_ip.address)
    ip_address.reserved = False
    ip_address.save()

    reserved_ips_list = client.networking.reserved_ips(
        ReservedIPAddress.address == reserved_ip.address
    )
    assert len(reserved_ips_list) == 0


def verify_nat_gateway(nat_gateway, nat_gateway_read):
    assert nat_gateway_read.id == nat_gateway.id
    assert nat_gateway_read.region.id == nat_gateway.region.id
    assert nat_gateway_read.label == nat_gateway.label
    assert len(nat_gateway_read.addresses) == 0
    assert nat_gateway_read.address_autoscale_max > 0
    assert nat_gateway_read.default_ports_per_interface == 4096
    assert nat_gateway_read.portset_assignments == 0
    assert nat_gateway_read.portset_capacity > 0


def verify_nat_gateway_address(nat_address, reserved_ip_address):
    assert nat_address.address == reserved_ip_address
    assert nat_address.in_use == False
    assert nat_address.interface_count == 0
    assert nat_address.interface_url.endswith(
        f"/{reserved_ip_address}/interfaces"
    )
    assert nat_address.portset_assignments == 0
    assert nat_address.portset_capacity > 0


def verify_nat_gateway_interface(interface, linode, reserved_ip):
    assert interface.id == linode.linode_interfaces[0].id
    assert interface.linode.id == linode.id
    assert interface.addresses[0] == reserved_ip.address
    assert interface.portsets[0].address == reserved_ip.address


@pytest.mark.smoke
def test_create_nat_gateway(test_linode_client, create_nat_gateway):
    client = test_linode_client

    gateway = client.load(NATGateway, create_nat_gateway.id)
    verify_nat_gateway(create_nat_gateway, gateway)

    gateways = client.networking.natgateways(
        NATGateway.label == create_nat_gateway.label
    )
    assert len(gateways) == 1
    verify_nat_gateway(create_nat_gateway, gateways[0])


def test_update_nat_gateway(test_linode_client, create_nat_gateway):
    client = test_linode_client
    gateway = create_nat_gateway

    new_label = f"{gateway.label}-updated"
    gateway.label = new_label
    gateway.save()

    gateway_updated = client.load(NATGateway, gateway.id)
    assert gateway_updated.label == new_label


@pytest.mark.parametrize("create_nat_gateway", [False], indirect=True)
def test_assign_nat_gateway_ip_address(
    test_linode_client, create_nat_gateway, create_reserved_ip
):
    gateway = create_nat_gateway
    reserved_ip = create_reserved_ip

    gateway.address_assignment_create(reserved_ip.address)

    addresses = gateway.address_assignments()
    assert len(addresses) == 1
    verify_nat_gateway_address(addresses[0], reserved_ip.address)

    address = gateway.address_assignment_view(reserved_ip.address)
    verify_nat_gateway_address(address, reserved_ip.address)

    gateway.address_assignment_delete(reserved_ip.address)
    addresses = gateway.address_assignments()
    assert len(addresses) == 0


@pytest.mark.parametrize("create_nat_gateway", [False], indirect=True)
def test_get_nat_gateway_linode_ifaces(
    test_linode_client,
    e2e_test_firewall,
    create_nat_gateway,
    create_nat_vpc_with_subnet_and_linode,
    create_reserved_ip,
):
    client = test_linode_client
    gateway = create_nat_gateway
    vpc, subnet, linode = create_nat_vpc_with_subnet_and_linode
    reserved_ip = create_reserved_ip

    gateway.address_assignment_create(reserved_ip.address)
    # Link the NAT Gateway to the VPC Subnet
    subnet.natgateway = VPCSubnetNATGatewayOptions(id=gateway.id)
    subnet.save()

    linode.interface_create(
        firewall_id=e2e_test_firewall,
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
    )
    linode = client.load(Instance, linode.id)

    gateway_ifaces = gateway.interfaces()
    assert len(gateway_ifaces) == 1
    verify_nat_gateway_interface(gateway_ifaces[0], linode, reserved_ip)

    gateway_ifaces = gateway.address_interfaces(reserved_ip.address)
    verify_nat_gateway_interface(gateway_ifaces[0], linode, reserved_ip)

    address = gateway.address_assignment_view(reserved_ip.address)
    assert address.in_use == True
    assert address.interface_count == 1
    assert address.portset_assignments == 1


def test_get_nat_gateway_types(test_linode_client):
    client = test_linode_client

    gateway_types = client.networking.natgateway_types()
    assert len(gateway_types) > 0
    assert gateway_types[0].id == "g1-natgateway"
    assert gateway_types[0].label == "NAT Gateway"
    assert (
        gateway_types[0].price.hourly >= 0
        or gateway_types[0].price.monthly >= 0
    )
    # TODO region_prices and transfer fields are not in use at the moment
    # assert isinstance(gateway_types[0].region_prices, list)
    # assert isinstance(gateway_types[0].transfer, int)


def test_get_nat_gateway_settings(test_linode_client):
    client = test_linode_client

    gateway_settings = client.networking.natgateway_settings()
    assert all(
        port in [4096, 8192, 16384]
        for port in gateway_settings.allowed_ports_per_interface
    )
    assert gateway_settings.maximum_autoscaling_addresses_per_natgateway > 0
    assert gateway_settings.maximum_reserved_addresses_per_natgateway > 0

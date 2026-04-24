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

from linode_api4 import Instance, LinodeClient, ApiError
from linode_api4.objects import Config, ConfigInterfaceIPv4, Firewall, IPAddress, ReservedIPAddress
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
    {"Linodes", "Cloud Firewall"},
    site_type="core",
)


def create_linode_func(test_linode_client):
    client = test_linode_client

    label = get_test_label()

    linode_instance, _ = client.linode.instance_create(
        "g6-nanode-1",
        TEST_REGION,
        image="linode/debian12",
        label=label,
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

    wait_for_condition(3, 100, get_status, linode, "running")

    retry_sending_request(3, linode.reboot)

    wait_for_condition(3, 100, get_status, linode, "rebooting")
    assert linode.status == "rebooting"

    wait_for_condition(3, 100, get_status, linode, "running")

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


@pytest.fixture
def create_reserved_ip(test_linode_client):
    client = test_linode_client
    reserved_ip = client.networking.reserved_ip_create(
        region=TEST_REGION,
        tags=["test1"]
    )

    yield reserved_ip

    # Delete only if IP exists (some tests delete it earlier)
    if client.networking.reserved_ips(ReservedIPAddress.address==reserved_ip.address):
        reserved_ip.delete()


@pytest.fixture
def create_reserved_ip_assigned(test_linode_client, create_linode):
    client = test_linode_client
    linode = create_linode
    reserved_ip = client.networking.reserved_ip_create(
        region=linode.region,
        tags=["test", "assigned"],
    )

    client.networking.ip_addresses_assign(
        assignments=[{"address": reserved_ip.address, "linode_id": linode.id}],
        region=linode.region,
    )

    reserved_ip = test_linode_client.load(ReservedIPAddress, reserved_ip.address)

    yield linode, reserved_ip

    # Delete only if IP exists (some tests delete it earlier)
    if client.networking.reserved_ips(ReservedIPAddress.address==reserved_ip.address):
        reserved_ip.delete()


def verify_reserved_ip(reserved_ip):
    assert isinstance(ipaddress.ip_address(reserved_ip.address), ipaddress.IPv4Address)
    assert reserved_ip.type == "ipv4"
    assert reserved_ip.public == True
    assert reserved_ip.reserved == True
    assert reserved_ip.linode_id is None
    assert reserved_ip.assigned_entity is None


def verify_reserved_ip_assigned(reserved_ip, resource):
    assert isinstance(ipaddress.ip_address(reserved_ip.address), ipaddress.IPv4Address)
    assert reserved_ip.type == "ipv4"
    assert reserved_ip.public == True
    assert reserved_ip.reserved == True
    assert reserved_ip.linode_id == resource.id
    assert reserved_ip.region.id == resource.region.id
    assert reserved_ip.assigned_entity.id == resource.id
    assert reserved_ip.assigned_entity.type == "linode"
    assert reserved_ip.assigned_entity.label == resource.label
    assert reserved_ip.assigned_entity.url == f"/v4/linode/instances/{resource.id}"


@pytest.mark.smoke
@pytest.mark.parametrize("region, tags", [
    (TEST_REGION, ["test"]),
    (TEST_REGION, None),
])
def test_create_reserved_ip(request, test_linode_client, region, tags):
    client = test_linode_client
    reserved_ip = client.networking.reserved_ip_create(
        region=region,
        tags=tags
    )
    request.addfinalizer(reserved_ip.delete)

    verify_reserved_ip(reserved_ip)
    # assert reserved_ip.tags == tags  # NOTE: Skipped as tags not available in the API yet


def test_create_reserved_ip_wo_region_fail(test_linode_client):
    client = test_linode_client

    with pytest.raises(ApiError) as exc_info:
        client.networking.reserved_ip_create(
            region=None,
            tags=["test"]
        )

    error_msg = str(exc_info.value.json)
    assert exc_info.value.status == 400
    assert "region is required" in error_msg


@pytest.mark.skip   # NOTE: Skipped as tags not available in the API yet
def test_update_reserved_ip_tags(test_linode_client, create_reserved_ip):
    client = test_linode_client
    reserved_ip = create_reserved_ip
    verify_reserved_ip(reserved_ip)
    assert reserved_ip.tags == ["test"]

    reserved_ip.tags = ["updated"]
    reserved_ip.save()
    reserved_ip = client.networking.reserved_ips(ReservedIPAddress.address==reserved_ip.address)[0]
    verify_reserved_ip(reserved_ip)
    assert reserved_ip.tags == ["updated"]


def test_create_reserved_ip_assigned(test_linode_client, create_reserved_ip_assigned):
    client = test_linode_client
    linode, reserved_ip = create_reserved_ip_assigned

    verify_reserved_ip_assigned(reserved_ip, linode)
    # assert reserved_ip.tags == tags  # NOTE: Skipped as tags not available in the API yet

    ips_list = client.networking.ips()
    assert reserved_ip.address in [ip.address for ip in ips_list]

    reserved_ips_list = client.networking.reserved_ips()
    assert reserved_ip.address in [ip.address for ip in reserved_ips_list]

    # linode_ips = linode.ips.ipv4.public
    # assert len(linode_ips) == 2
    # assert any([ip.reserved for ip in linode_ips])

    reserved_ip.delete()
    reserved_ips_list = client.networking.reserved_ips()
    assert reserved_ip.address not in [ip.address for ip in reserved_ips_list]

    reserved_ips_list = client.networking.reserved_ips(ReservedIPAddress.address==reserved_ip.address)
    assert len(reserved_ips_list) == 0

    # delattr(linode, "_ips")
    # linode_ips = linode.ips.ipv4.public
    # assert len(linode_ips) == 2
    # assert not any([ip.reserved for ip in linode_ips])
    # assert not any([ip.tags for ip in linode_ips])  # Tags should be removed ???


def test_get_reserved_ip_types(test_linode_client, create_reserved_ip):
    # TODO: Currently it uses client (token), should not it be publicly accessible (no token required) ???
    client = test_linode_client
    types = client.networking.reserved_ip_types()
    assert types.only

    pricing = types.first()
    assert pricing.id == "reserved-ipv4"
    assert pricing.label == "Reserved IPv4"
    assert pricing.price.hourly
    # assert pricing.price.monthly is None
    # assert pricing.region_prices == []


@pytest.mark.smoke
@pytest.mark.parametrize("reserved, region", [
    (True, TEST_REGION),
    (True, None),
])
def test_create_reserved_ip_with_allocate(test_linode_client, create_linode, reserved, region):
    client = test_linode_client
    linode = create_linode

    if region:
        reserved_ip = client.networking.ip_allocate(reserved=reserved, region=TEST_REGION)
        verify_reserved_ip(reserved_ip)
    else:
        reserved_ip = client.networking.ip_allocate(reserved=reserved, linode=linode.id)
        verify_reserved_ip_assigned(reserved_ip, linode)

    # assert reserved_ip.tags == tags  # NOTE: Skipped as tags not available in the API yet


def test_create_reserved_ip_with_allocate_fail(test_linode_client, create_linode):
    client = test_linode_client
    linode = create_linode
    region = TEST_REGION

    while region == linode.region:
        region = get_region(
            LinodeClient(
                token=get_token(),
                base_url=get_api_url(),
                ca_path=get_api_ca_file(),
            ),
            {"Linodes", "Cloud Firewall"},
            site_type="core",
        )

    with pytest.raises(ApiError) as exc_info:
        client.networking.ip_allocate(reserved=True, region=region, linode=linode.id)

    error_msg = str(exc_info.value.json)
    assert exc_info.value.status == 400
    assert "Region passed in must match Linode's region" in error_msg


def test_reserve_ephemeral_ip(test_linode_client, create_linode):
    client = test_linode_client
    linode = create_linode

    ip_address = client.load(IPAddress, linode.ipv4[0])
    assert ip_address.linode_id == linode.id
    assert ip_address.reserved == False

    ip_address.reserved = True
    # ip_address.rdns = "test.example.org"  # TODO: Should be enabled ?
    ip_address.save()
    ip_address = client.load(IPAddress, linode.ipv4[0])
    assert ip_address.linode_id == linode.id
    assert ip_address.reserved == True

    ip_address.reserved = False
    ip_address.save()
    ip_address = client.load(IPAddress, linode.ipv4[0])
    assert ip_address.linode_id == linode.id
    assert ip_address.reserved == False


def test_convert_unassigned_reserved_ip_to_ephemeral(test_linode_client, create_reserved_ip):
    client = test_linode_client
    reserved_ip = create_reserved_ip
    verify_reserved_ip(reserved_ip)

    ip_address = client.load(IPAddress, reserved_ip.address)
    ip_address.reserved = False
    ip_address.save()

    reserved_ips_list = client.networking.reserved_ips(ReservedIPAddress.address==reserved_ip.address)
    assert len(reserved_ips_list) == 0

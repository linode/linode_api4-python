import time
from test.integration.helpers import (
    get_test_label,
    retry_sending_request,
    send_request_when_resource_available,
    wait_for_condition,
)

import pytest

from linode_api4.errors import ApiError
from linode_api4.objects import (
    Config,
    ConfigInterface,
    ConfigInterfaceIPv4,
    Disk,
    Image,
    Instance,
    Type,
)


@pytest.fixture(scope="session")
def linode_with_volume_firewall(test_linode_client):
    client = test_linode_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    label = get_test_label()

    rules = {
        "outbound": [],
        "outbound_policy": "DROP",
        "inbound": [],
        "inbound_policy": "ACCEPT",
    }

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1",
        chosen_region,
        image="linode/debian10",
        label=label + "_modlinode",
    )

    volume = client.volume_create(
        label=label + "_volume",
        region=linode_instance.region.id,
        linode=linode_instance.id,
    )

    firewall = client.networking.firewall_create(
        label=label + "_firewall", rules=rules, status="enabled"
    )

    firewall.device_create(int(linode_instance.id))

    yield linode_instance

    firewall.delete()

    volume.detach()
    # wait for volume detach, can't currently get the attached/unattached status via SDK
    time.sleep(30)

    volume.delete()

    linode_instance.delete()


@pytest.fixture(scope="session")
def linode_for_network_interface_tests(test_linode_client):
    client = test_linode_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    timestamp = str(time.time_ns())
    label = "TestSDK-" + timestamp

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1", chosen_region, image="linode/debian10", label=label
    )

    yield linode_instance

    linode_instance.delete()


@pytest.fixture(scope="session", autouse=True)
def linode_for_disk_tests(test_linode_client):
    client = test_linode_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    label = get_test_label()

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1",
        chosen_region,
        image="linode/debian10",
        label=label + "_long_tests",
    )

    time.sleep(10)

    # Provisioning time
    wait_for_condition(10, 300, get_status, linode_instance, "running")

    time.sleep(10)

    linode_instance.shutdown()

    wait_for_condition(10, 100, get_status, linode_instance, "offline")

    yield linode_instance

    linode_instance.delete()


@pytest.mark.smoke
@pytest.fixture
def create_linode_for_long_running_tests(test_linode_client):
    client = test_linode_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    label = get_test_label()

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1",
        chosen_region,
        image="linode/debian10",
        label=label + "_long_tests",
    )

    yield linode_instance

    linode_instance.delete()


# Test helper
def get_status(linode: Instance, status: str):
    return linode.status == status


def test_get_linode(test_linode_client, linode_with_volume_firewall):
    linode = test_linode_client.load(Instance, linode_with_volume_firewall.id)

    assert linode.label == linode_with_volume_firewall.label
    assert linode.id == linode_with_volume_firewall.id


def test_linode_transfer(test_linode_client, linode_with_volume_firewall):
    linode = test_linode_client.load(Instance, linode_with_volume_firewall.id)

    transfer = linode.transfer

    assert "used" in str(transfer)
    assert "quota" in str(transfer)
    assert "billable" in str(transfer)


def test_linode_rebuild(test_linode_client):
    client = test_linode_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    label = get_test_label() + "_rebuild"

    linode, password = client.linode.instance_create(
        "g6-nanode-1", chosen_region, image="linode/debian10", label=label
    )

    wait_for_condition(10, 100, get_status, linode, "running")

    retry_sending_request(3, linode.rebuild, "linode/debian10")

    wait_for_condition(10, 100, get_status, linode, "rebuilding")

    assert linode.status == "rebuilding"
    assert linode.image.id == "linode/debian10"

    wait_for_condition(10, 300, get_status, linode, "running")

    assert linode.status == "running"

    linode.delete()


def test_linode_available_backups(create_linode):
    linode = create_linode

    enable_backup = linode.enable_backups()
    backups = linode.backups

    assert enable_backup
    assert "enabled" in str(backups)
    assert "available" in str(backups)
    assert "schedule" in str(backups)
    assert "last_successful" in str(backups)


def test_update_linode(create_linode):
    linode = create_linode
    new_label = get_test_label() + "_updated"
    linode.label = new_label
    linode.group = "new_group"
    updated = linode.save()

    assert updated
    assert linode.label == new_label


def test_delete_linode(test_linode_client):
    client = test_linode_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    label = get_test_label()

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1",
        chosen_region,
        image="linode/debian10",
        label=label + "_linode",
    )

    linode_instance.delete()


def test_linode_reboot(create_linode):
    linode = create_linode

    wait_for_condition(3, 100, get_status, linode, "running")

    retry_sending_request(3, linode.reboot)

    wait_for_condition(3, 100, get_status, linode, "rebooting")
    assert linode.status == "rebooting"

    wait_for_condition(3, 100, get_status, linode, "running")
    assert linode.status == "running"


def test_linode_shutdown(create_linode):
    linode = create_linode

    wait_for_condition(10, 100, get_status, linode, "running")

    retry_sending_request(3, linode.shutdown)

    wait_for_condition(10, 100, get_status, linode, "offline")

    assert linode.status == "offline"


def test_linode_boot(create_linode):
    linode = create_linode

    if linode.status != "offline":
        retry_sending_request(3, linode.shutdown)
        wait_for_condition(3, 100, get_status, linode, "offline")
        retry_sending_request(3, linode.boot)
    else:
        retry_sending_request(3, linode.boot)

    wait_for_condition(10, 100, get_status, linode, "running")

    assert linode.status == "running"


def test_linode_resize(create_linode_for_long_running_tests):
    linode = create_linode_for_long_running_tests

    wait_for_condition(10, 100, get_status, linode, "running")

    retry_sending_request(3, linode.resize, "g6-standard-6")

    wait_for_condition(10, 100, get_status, linode, "resizing")

    assert linode.status == "resizing"

    # Takes about 3-5 minute to resize, sometimes longer...
    wait_for_condition(30, 600, get_status, linode, "running")

    assert linode.status == "running"


def test_linode_resize_with_class(
    test_linode_client, create_linode_for_long_running_tests
):
    linode = create_linode_for_long_running_tests
    ltype = Type(test_linode_client, "g6-standard-6")

    wait_for_condition(10, 100, get_status, linode, "running")

    time.sleep(5)
    res = linode.resize(new_type=ltype)

    assert res

    wait_for_condition(10, 300, get_status, linode, "resizing")

    assert linode.status == "resizing"

    # Takes about 3-5 minute to resize, sometimes longer...
    wait_for_condition(30, 600, get_status, linode, "running")

    assert linode.status == "running"


def test_linode_boot_with_config(create_linode):
    linode = create_linode

    wait_for_condition(10, 100, get_status, linode, "running")
    retry_sending_request(3, linode.shutdown)

    wait_for_condition(30, 300, get_status, linode, "offline")

    config = linode.configs[0]

    retry_sending_request(3, linode.boot, config)

    wait_for_condition(10, 100, get_status, linode, "running")

    assert linode.status == "running"


def test_linode_firewalls(linode_with_volume_firewall):
    linode = linode_with_volume_firewall

    firewalls = linode.firewalls()

    assert len(firewalls) > 0
    assert "TestSDK" in firewalls[0].label


def test_linode_volumes(linode_with_volume_firewall):
    linode = linode_with_volume_firewall

    volumes = linode.volumes()

    assert len(volumes) > 0
    assert "TestSDK" in volumes[0].label


def wait_for_disk_status(disk: Disk, timeout):
    start_time = time.time()
    while True:
        try:
            if disk.status == "ready":
                return disk.status
        except ApiError:
            if time.time() - start_time > timeout:
                raise TimeoutError("Wait for condition timeout error")


@pytest.mark.dependency()
def test_disk_resize_and_duplicate(test_linode_client, linode_for_disk_tests):
    linode = linode_for_disk_tests

    disk = linode.disks[0]

    disk.resize(5000)

    # Using hard sleep instead of wait as the status shows ready when it is resizing
    time.sleep(120)

    disk = test_linode_client.load(Disk, linode.disks[0].id, linode.id)

    assert disk.size == 5000

    dup_disk = disk.duplicate()

    time.sleep(40)

    wait_for_disk_status(dup_disk, 120)

    assert dup_disk.linode_id == linode.id


@pytest.mark.dependency(depends=["test_disk_resize_and_duplicate"])
def test_linode_create_disk(test_linode_client, linode_for_disk_tests):
    linode = test_linode_client.load(Instance, linode_for_disk_tests.id)

    disk = linode.disk_create(size=500)

    wait_for_disk_status(disk, 120)

    assert disk.linode_id == linode.id


def test_linode_instance_password(create_linode_for_pass_reset):
    linode = create_linode_for_pass_reset[0]
    password = create_linode_for_pass_reset[1]

    wait_for_condition(10, 100, get_status, linode, "running")

    retry_sending_request(3, linode.shutdown)

    wait_for_condition(10, 200, get_status, linode, "offline")

    linode.reset_instance_root_password(root_password=password)

    linode.boot()

    wait_for_condition(10, 100, get_status, linode, "running")

    assert linode.status == "running"


def test_linode_ips(create_linode):
    linode = create_linode

    ips = linode.ips

    assert ips.ipv4.public[0].address == linode.ipv4[0]


def test_linode_initate_migration(test_linode_client):
    client = test_linode_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    label = get_test_label() + "_migration"

    linode, password = client.linode.instance_create(
        "g6-nanode-1", chosen_region, image="linode/debian10", label=label
    )

    wait_for_condition(10, 100, get_status, linode, "running")
    # Says it could take up to ~6 hrs for migration to fully complete

    send_request_when_resource_available(
        300, linode.initiate_migration, "us-central"
    )

    res = linode.delete()

    assert res


def test_config_update_interfaces(create_linode):
    linode = create_linode
    config = linode.configs[0]

    new_interfaces = [
        {"purpose": "public"},
        ConfigInterface(
            purpose="vlan", label="cool-vlan", ipam_address="10.0.0.4/32"
        ),
    ]
    config.interfaces = new_interfaces

    res = config.save()
    config.invalidate()

    assert res
    assert config.interfaces[0].purpose == "public"
    assert config.interfaces[1].purpose == "vlan"
    assert config.interfaces[1].label == "cool-vlan"
    assert config.interfaces[1].ipam_address == "10.0.0.4/32"


def test_get_config(test_linode_client, create_linode):
    linode = create_linode

    config = test_linode_client.load(Config, linode.configs[0].id, linode.id)

    assert config.id == linode.configs[0].id


def test_get_linode_types(test_linode_client):
    types = test_linode_client.linode.types()

    ids = [i.id for i in types]

    assert len(types) > 0
    assert "g6-nanode-1" in ids


def test_get_linode_types_overrides(test_linode_client):
    types = test_linode_client.linode.types()

    target_types = [
        v
        for v in types
        if len(v.region_prices) > 0 and v.region_prices[0].hourly > 0
    ]

    assert len(target_types) > 0

    for linode_type in target_types:
        assert linode_type.region_prices[0].hourly >= 0
        assert linode_type.region_prices[0].monthly >= 0


def test_save_linode_noforce(test_linode_client, create_linode):
    linode = create_linode
    old_label = linode.label
    linode.label = "updated_no_force_label"
    linode.save(force=False)

    linode = test_linode_client.load(Instance, linode.id)

    assert old_label != linode.label


def test_save_linode_force(test_linode_client, create_linode):
    linode = create_linode
    old_label = linode.label
    linode.label = "updated_force_label"
    linode.save(force=False)

    linode = test_linode_client.load(Instance, linode.id)

    assert old_label != linode.label


class TestNetworkInterface:
    def test_list(self, linode_for_network_interface_tests):
        linode = linode_for_network_interface_tests

        config: Config = linode.configs[0]

        config.interface_create_public(
            primary=True,
        )

        label = str(time.time_ns()) + "vlabel"

        config.interface_create_vlan(label=label, ipam_address="10.0.0.3/32")

        interface = config.network_interfaces

        assert interface[0].purpose == "public"
        assert interface[0].primary
        assert interface[1].purpose == "vlan"
        assert interface[1].label == label
        assert interface[1].ipam_address == "10.0.0.3/32"

    def test_create_public(self, linode_for_network_interface_tests):
        linode = linode_for_network_interface_tests

        config: Config = linode.configs[0]

        config.interfaces = []
        config.save()

        interface = config.interface_create_public(
            primary=True,
        )

        config.invalidate()

        assert interface.id == config.interfaces[0].id
        assert interface.purpose == "public"
        assert interface.primary

    def test_create_vlan(self, linode_for_network_interface_tests):
        linode = linode_for_network_interface_tests

        config: Config = linode.configs[0]

        config.interfaces = []
        config.save()

        interface = config.interface_create_vlan(
            label="testvlan", ipam_address="10.0.0.2/32"
        )

        config.invalidate()

        assert interface.id == config.interfaces[0].id
        assert interface.purpose == "vlan"
        assert interface.label == "testvlan"
        assert interface.ipam_address == "10.0.0.2/32"

    def test_create_vpc(
        self,
        linode_for_network_interface_tests,
        create_vpc_with_subnet_and_linode,
    ):
        vpc, subnet, linode, _ = create_vpc_with_subnet_and_linode

        config: Config = linode.configs[0]

        config.interfaces = []
        config.save()

        interface = config.interface_create_vpc(
            subnet=subnet,
            primary=True,
            ipv4=ConfigInterfaceIPv4(vpc="10.0.0.2", nat_1_1="any"),
            ip_ranges=["10.0.0.5/32"],
        )

        config.invalidate()

        assert interface.id == config.interfaces[0].id
        assert interface.subnet.id == subnet.id
        assert interface.purpose == "vpc"
        assert interface.ipv4.vpc == "10.0.0.2"
        assert interface.ipv4.nat_1_1 == linode.ipv4[0]
        assert interface.ip_ranges == ["10.0.0.5/32"]

    def test_update_vpc(
        self,
        linode_for_network_interface_tests,
        create_vpc_with_subnet_and_linode,
    ):
        vpc, subnet, linode, _ = create_vpc_with_subnet_and_linode

        config: Config = linode.configs[0]

        config.interfaces = []
        config.save()

        interface = config.interface_create_vpc(
            subnet=subnet,
            primary=True,
            ip_ranges=["10.0.0.5/32"],
        )

        interface.primary = False
        interface.ip_ranges = ["10.0.0.6/32"]
        interface.ipv4.vpc = "10.0.0.3"
        interface.ipv4.nat_1_1 = "any"

        interface.save()
        interface.invalidate()
        config.invalidate()

        assert interface.id == config.interfaces[0].id
        assert interface.subnet.id == subnet.id
        assert interface.purpose == "vpc"
        assert interface.ipv4.vpc == "10.0.0.3"
        assert interface.ipv4.nat_1_1 == linode.ipv4[0]
        assert interface.ip_ranges == ["10.0.0.6/32"]

    def test_reorder(self, linode_for_network_interface_tests):
        linode = linode_for_network_interface_tests

        config: Config = linode.configs[0]

        pub_interface = config.interface_create_public(
            primary=True,
        )

        label = str(time.time_ns()) + "vlabel"
        vlan_interface = config.interface_create_vlan(
            label=label, ipam_address="10.0.0.3/32"
        )

        send_request_when_resource_available(300, linode.shutdown)

        interfaces = config.network_interfaces
        interfaces.reverse()

        send_request_when_resource_available(
            300, config.interface_reorder, interfaces
        )
        config.invalidate()

        assert [v.id for v in config.interfaces[:2]] == [
            vlan_interface.id,
            pub_interface.id,
        ]

    def test_delete_interface_containing_vpc(
        self, create_vpc_with_subnet_and_linode
    ):
        vpc, subnet, linode, _ = create_vpc_with_subnet_and_linode

        config: Config = linode.configs[0]

        config.interfaces = []

        # must power off linode before saving
        send_request_when_resource_available(300, linode.shutdown)

        send_request_when_resource_available(60, config.save)

        interface = config.interface_create_vpc(
            subnet=subnet,
            primary=True,
            ip_ranges=["10.0.0.8/32"],
        )

        result = interface.delete()

        # returns true when delete successful
        assert result

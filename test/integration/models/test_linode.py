import time
from test.integration.helpers import (
    get_test_label,
    retry_sending_request,
    wait_for_condition,
)

import pytest

from linode_api4.errors import ApiError
from linode_api4.objects import Config, Disk, Image, Instance, Type


@pytest.fixture(scope="session")
def create_linode_with_volume_firewall(get_client):
    client = get_client
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
        "g5-standard-4",
        chosen_region,
        image="linode/debian9",
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

    linode_instance.delete()

    volume.detach()
    # wait for volume detach, can't currently get the attach/unattached status via SDK
    time.sleep(30)

    volume.delete()


@pytest.mark.smoke
@pytest.fixture
def create_linode_for_long_running_tests(get_client):
    client = get_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    label = get_test_label()

    linode_instance, password = client.linode.instance_create(
        "g5-standard-4",
        chosen_region,
        image="linode/debian9",
        label=label + "_long_tests",
    )

    yield linode_instance

    linode_instance.delete()


# Test helper
def get_status(linode: Instance, status: str):
    return linode.status == status


def test_get_linode(get_client, create_linode_with_volume_firewall):
    linode = get_client.load(Instance, create_linode_with_volume_firewall.id)

    assert linode.label == create_linode_with_volume_firewall.label
    assert linode.id == create_linode_with_volume_firewall.id


def test_linode_transfer(get_client, create_linode_with_volume_firewall):
    linode = get_client.load(Instance, create_linode_with_volume_firewall.id)

    transfer = linode.transfer

    assert "used" in str(transfer)
    assert "quota" in str(transfer)
    assert "billable" in str(transfer)


def test_linode_rebuild(get_client):
    client = get_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    label = get_test_label() + "_rebuild"

    linode, password = client.linode.instance_create(
        "g5-standard-4", chosen_region, image="linode/debian9", label=label
    )

    wait_for_condition(10, 100, get_status, linode, "running")

    retry_sending_request(3, linode.rebuild, "linode/debian9")

    wait_for_condition(10, 100, get_status, linode, "rebuilding")

    assert linode.status == "rebuilding"
    assert linode.image.id == "linode/debian9"

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


def test_delete_linode(get_client):
    client = get_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    label = get_test_label()

    linode_instance, password = client.linode.instance_create(
        "g5-standard-4",
        chosen_region,
        image="linode/debian9",
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
    get_client, create_linode_for_long_running_tests
):
    linode = create_linode_for_long_running_tests
    ltype = Type(get_client, "g6-standard-6")

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


def test_linode_firewalls(create_linode_with_volume_firewall):
    linode = create_linode_with_volume_firewall

    firewalls = linode.firewalls()

    assert len(firewalls) > 0
    assert "TestSDK" in firewalls[0].label


def test_linode_volumes(create_linode_with_volume_firewall):
    linode = create_linode_with_volume_firewall

    volumes = linode.volumes()

    assert len(volumes) > 0
    assert "TestSDK" in volumes[0].label


def test_linode_disk_duplicate(get_client, create_linode):
    pytest.skip("Need to find out the space sizing when duplicating disks")
    linode = create_linode

    disk = get_client.load(Disk, linode.disks[0].id, linode.id)

    try:
        dup_disk = disk.duplicate()
        assert dup_disk.linode_id == linode.id
    except ApiError as e:
        assert e.status == 400
        assert "Insufficient space" in str(e.json)


def test_linode_instance_password(create_linode_for_pass_reset):
    pytest.skip("Failing due to mismatched request body")
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


def test_linode_initate_migration(get_client):
    client = get_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    label = get_test_label() + "_migration"

    linode, password = client.linode.instance_create(
        "g5-standard-4", chosen_region, image="linode/debian9", label=label
    )

    wait_for_condition(10, 100, get_status, linode, "running")
    # Says it could take up to ~6 hrs for migration to fully complete
    linode.initiate_migration(region="us-central")

    res = linode.delete()

    assert res


def test_linode_create_disk(create_linode):
    pytest.skip(
        "Pre-requisite for the test account need to comply with this test"
    )
    linode = create_linode
    disk, gen_pass = linode.disk_create()


def test_disk_resize():
    pytest.skip(
        "Pre-requisite for the test account need to comply with this test"
    )


def test_config_update_interfaces(create_linode):
    linode = create_linode
    new_interfaces = [
        {"purpose": "public"},
        {"purpose": "vlan", "label": "cool-vlan"},
    ]

    config = linode.configs[0]

    config.interfaces = new_interfaces

    res = config.save()

    assert res
    assert "cool-vlan" in str(config.interfaces)


def test_get_config(get_client, create_linode):
    pytest.skip(
        "Model get method: client.load(Config, 123, 123) does not work..."
    )
    linode = create_linode
    json = get_client.get(
        "linode/instances/"
        + str(linode.id)
        + "/configs/"
        + str(linode.configs[0].id)
    )
    config = Config(get_client, linode.id, linode.configs[0].id, json=json)

    assert config.id == linode.configs[0].id


def test_get_linode_types(get_client):
    types = get_client.linode.types()

    ids = [i.id for i in types]

    assert len(types) > 0
    assert "g6-nanode-1" in ids


def test_get_linode_type_by_id(get_client):
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )


def test_get_linode_type_gpu():
    pytest.skip(
        "Might need Type to match how other object models are behaving e.g. client.load(Type, 123)"
    )


def test_save_linode_noforce(get_client, create_linode):
    linode = create_linode
    old_label = linode.label
    linode.label = "updated_no_force_label"
    linode.save(force=False)

    linode = get_client.load(Instance, linode.id)

    assert old_label != linode.label


def test_save_linode_force(get_client, create_linode):
    linode = create_linode
    old_label = linode.label
    linode.label = "updated_force_label"
    linode.save(force=False)

    linode = get_client.load(Instance, linode.id)

    assert old_label != linode.label

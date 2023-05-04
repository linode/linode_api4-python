import pytest

from test.integration.helpers import get_test_label, wait_for_condition
from linode_api4.objects import Config, Disk, Image, Instance, Type
from linode_api4.errors import ApiError

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
        "g5-standard-4", chosen_region, image="linode/debian9", label=label+"_linode"
    )

    volume = client.volume_create(label=label+"_volume", region=linode_instance.region.id, linode=linode_instance.id)

    firewall = client.networking.firewall_create(label=label+"_firewall", rules=rules, status="enabled")

    firewall.device_create(int(linode_instance.id))

    yield client, linode_instance

    linode_instance.delete()
    volume.delete()
    firewall.delete()


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


def test_linode_rebuild(create_linode):
    linode = create_linode

    linode.rebuild("linode/debian9")

    def get_running_status():
        return linode.status == 'running'

    wait_for_condition(15, 100, get_running_status)

    assert linode.status == 'running'
    assert linode.image.id == 'linode/debian9'


def test_linode_available_backups(create_linode):
    linode = create_linode

    enable_backup = linode.enable_bakcups()
    backups = linode.backups

    assert enable_backup
    assert "enabled" in str(backups)
    assert "available" in str(backups)
    assert "schedule" in str(backups)
    assert "last_successful" in str(backups)

def test_update_linode(create_linode):
    linode = create_linode
    new_label = get_test_label()+ "+updated"
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
        "g5-standard-4", chosen_region, image="linode/debian9", label=label+"_linode"
    )

    linode_instance.delete()

def test_linode_reboot(create_linode):
    linode = create_linode

    linode.reboot()

    assert linode.status == 'rebooting'

    def get_running_status():
        linode.status == 'running'

    wait_for_condition(10, 100, get_running_status)

    assert linode.status == 'running'

def test_linode_shutdown(create_linode):
    linode = create_linode

    linode.shutdown()

    assert linode.status == 'shutting_down'

    def get_offline_status():
        linode.status == 'offline'

    wait_for_condition(10, 100, get_offline_status)

    assert linode.status == 'offline'


def test_linode_boot(create_linode):
    linode = create_linode

    def get_offline_status():
        linode.status == 'offline'

    def get_running_status():
        linode.status == 'running'

    if linode.status != 'offline':
        linode.shutdown()
        wait_for_condition(10, 100, get_offline_status)
        linode.boot()
    else:
        linode.boot()

    wait_for_condition(10, 100, get_running_status)


    assert linode.status == 'running'


def test_linode_resize(create_linode):
    linode = create_linode

    linode.resize('g6-standard-6')

    def get_resizing_status():
        linode.status == 'resizing'

    def get_running_status():
        linode.status == 'running'

    wait_for_condition(10, 100, get_resizing_status)

    assert linode.status == 'resizing'

    # Takes about 3-5 minute to resize
    wait_for_condition(30, 300, get_running_status)

    assert linode.status == 'running'

def test_linode_resize_with_class(get_client ,create_linode):
    linode = create_linode
    ltype = Type(get_client, 'g6-standard-4')
    linode.resize(ltype)

    def get_resizing_status():
        linode.status == 'resizing'

    def get_running_status():
        linode.status == 'running'

    wait_for_condition(10, 100, get_resizing_status)

    assert linode.status == 'resizing'

    # Takes about 3-5 minute to resize
    wait_for_condition(30, 300, get_running_status)

    assert linode.status == 'running'


def test_linode_boot_with_config(create_linode):
    linode = create_linode

    linode.shutdown()
    def get_offline_status():
        linode.status == 'offline'

    def get_running_status():
        linode.status == 'running'

    wait_for_condition(10, 100, get_offline_status)
    config = linode.config[0]

    linode.boot(config=config)

    wait_for_condition(10, 100, get_running_status)

    assert linode.status == 'running'


def test_linode_firewalls(create_linode_with_volume_firewall):
    linode = create_linode_with_volume_firewall

    firewalls = linode.firewalls()

    assert(len(firewalls) > 0)
    assert("IntSDK" in firewalls[0].label)


def test_linode_volumes(create_linode_with_volume_firewall):
    linode = create_linode_with_volume_firewall

    volumes = linode.volumes()

    assert(len(volumes) > 0 )
    assert("IntSDK" in volumes[0].label)


# Need to find out the space sizing when duplicating disks
def test_linode_disk_duplicate(get_client, create_linode):
    linode = create_linode

    disk = get_client.load(Disk, linode.disks[0].id, linode.id)

    try:
        dup_disk = disk.duplicate()
        assert dup_disk.linode_id == linode.id
    except ApiError as e:
        assert e.status == 400
        assert "Insufficient space" in str(e.json)


def test_linode_instance_password(create_linode):
    linode = create_linode

    linode.shutdown()
    def get_offline_status():
        linode.status == 'offline'

    def get_running_status():
        linode.status == 'running'

    wait_for_condition(10, 100, get_offline_status)

    linode.reset_root_password()

    linode.boot()

    wait_for_condition(10, 100, get_running_status)

    assert(linode.status == 'running')


def test_linode_ips(create_linode):
    linode = create_linode

    ips = linode.ips
#
# def test_linode_initate_migration():
#
#
# def test_linode_create_disk():
#
#
# def test_disk_resize():
#
#
# def test_config_update_interfaces():
#
#
# def test_get_config():
#
#
# def test_get_linode_types():
#
#
# def test_get_linode_type_by_id():
#
#
# def test_get_linode_type_gpu():
#
#
# def test_save_linode_noforce():
#
# def test_save_linode_force():
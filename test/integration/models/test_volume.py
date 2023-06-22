import time
from test.integration.conftest import get_token
from test.integration.helpers import (
    get_test_label,
    retry_sending_request,
    wait_for_condition,
)

import pytest

from linode_api4 import LinodeClient
from linode_api4.objects import Volume


@pytest.fixture(scope="session")
def create_linode_for_volume(get_client):
    client = get_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    timestamp = str(int(time.time()))
    label = "TestSDK-" + timestamp

    linode_instance, password = client.linode.instance_create(
        "g5-standard-4", chosen_region, image="linode/debian9", label=label
    )

    yield linode_instance

    linode_instance.delete()


def get_status(volume: Volume, status: str):
    client = LinodeClient(token=get_token())
    volume = client.load(Volume, volume.id)
    return volume.status == status


@pytest.mark.smoke
def test_get_volume(get_client, create_volume):
    volume = get_client.load(Volume, create_volume.id)

    assert volume.id == create_volume.id


def test_update_volume_tag(get_client, create_volume):
    volume = create_volume
    tag_1 = "volume_test_tag1"
    tag_2 = "volume_test_tag2"

    volume.tags = [tag_1, tag_2]
    volume.save()

    volume = get_client.load(Volume, create_volume.id)

    assert [tag_1, tag_2] == volume.tags


def test_volume_resize(get_client, create_volume):
    volume = get_client.load(Volume, create_volume.id)

    wait_for_condition(10, 100, get_status, volume, "active")

    res = retry_sending_request(5, volume.resize, 21)

    assert res


def test_volume_clone_and_delete(get_client, create_volume):
    volume = get_client.load(Volume, create_volume.id)
    label = get_test_label()

    wait_for_condition(10, 100, get_status, volume, "active")

    new_volume = retry_sending_request(5, volume.clone, label)

    assert label == new_volume.label

    res = retry_sending_request(5, new_volume.delete)

    assert res, "new volume deletion failed"


def test_attach_volume_to_linode(
    get_client, create_volume, create_linode_for_volume
):
    volume = create_volume
    linode = create_linode_for_volume

    res = retry_sending_request(5, volume.attach, linode.id)

    assert res


def test_detach_volume_to_linode(
    get_client, create_volume, create_linode_for_volume
):
    volume = create_volume
    linode = create_linode_for_volume

    res = retry_sending_request(5, volume.detach)

    assert res

    # time wait for volume to detach before deletion occurs
    time.sleep(30)

import time
from test.integration.conftest import get_token
from test.integration.helpers import (
    get_test_label,
    retry_sending_request,
    wait_for_condition,
)

import pytest

from linode_api4 import ApiError, LinodeClient
from linode_api4.objects import Volume


@pytest.fixture(scope="session")
def linode_for_volume(test_linode_client):
    client = test_linode_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    timestamp = str(time.time_ns())
    label = "TestSDK-" + timestamp

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1", chosen_region, image="linode/debian10", label=label
    )

    yield linode_instance

    timeout = 100  # give 100s for volume to be detached before deletion

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            res = linode_instance.delete()

            if res:
                break
            else:
                time.sleep(3)
        except ApiError as e:
            if time.time() - start_time > timeout:
                raise e


def get_status(volume: Volume, status: str):
    client = LinodeClient(token=get_token())
    volume = client.load(Volume, volume.id)
    return volume.status == status


@pytest.mark.smoke
def test_get_volume(test_linode_client, test_volume):
    volume = test_linode_client.load(Volume, test_volume.id)

    assert volume.id == test_volume.id


def test_update_volume_tag(test_linode_client, test_volume):
    volume = test_volume
    tag_1 = "volume_test_tag1"
    tag_2 = "volume_test_tag2"

    volume.tags = [tag_1, tag_2]
    volume.save()

    volume = test_linode_client.load(Volume, test_volume.id)

    assert [tag_1, tag_2] == volume.tags


def test_volume_resize(test_linode_client, test_volume):
    volume = test_linode_client.load(Volume, test_volume.id)

    wait_for_condition(10, 100, get_status, volume, "active")

    res = retry_sending_request(5, volume.resize, 21)

    assert res


def test_volume_clone_and_delete(test_linode_client, test_volume):
    volume = test_linode_client.load(Volume, test_volume.id)
    label = get_test_label()

    wait_for_condition(10, 100, get_status, volume, "active")

    new_volume = retry_sending_request(5, volume.clone, label)

    assert label == new_volume.label

    res = retry_sending_request(5, new_volume.delete)

    assert res, "new volume deletion failed"


def test_attach_volume_to_linode(
    test_linode_client, test_volume, linode_for_volume
):
    volume = test_volume
    linode = linode_for_volume

    res = retry_sending_request(5, volume.attach, linode.id)

    assert res


def test_detach_volume_to_linode(
    test_linode_client, test_volume, linode_for_volume
):
    volume = test_volume
    linode = linode_for_volume

    res = retry_sending_request(5, volume.detach)

    assert res

    # time wait for volume to detach before deletion occurs
    time.sleep(30)

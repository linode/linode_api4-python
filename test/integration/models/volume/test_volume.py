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
    send_request_when_resource_available,
    wait_for_condition,
)

import pytest

from linode_api4 import LinodeClient
from linode_api4.objects import RegionPrice, Volume, VolumeType

TEST_REGION = get_region(
    LinodeClient(
        token=get_token(),
        base_url=get_api_url(),
        ca_path=get_api_ca_file(),
    ),
    {"Linodes", "Cloud Firewall"},
    site_type="core",
)


@pytest.fixture(scope="session")
def test_volume(test_linode_client):
    client = test_linode_client
    label = get_test_label(length=8)

    volume = client.volume_create(label=label, region=TEST_REGION)

    yield volume

    send_request_when_resource_available(timeout=100, func=volume.delete)


@pytest.fixture(scope="session")
def linode_for_volume(test_linode_client, e2e_test_firewall):
    client = test_linode_client

    label = get_test_label(length=8)

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1",
        TEST_REGION,
        image="linode/debian12",
        label=label,
        firewall=e2e_test_firewall,
    )

    yield linode_instance

    send_request_when_resource_available(
        timeout=100, func=linode_instance.delete
    )


def get_status(volume: Volume, status: str):
    client = LinodeClient(
        token=get_token(),
        base_url=get_api_url(),
        ca_path=get_api_ca_file(),
    )
    volume = client.load(Volume, volume.id)
    return volume.status == status


@pytest.mark.smoke
def test_get_volume(test_linode_client, test_volume):
    volume = test_linode_client.load(Volume, test_volume.id)

    assert volume.id == test_volume.id


def test_get_volume_with_encryption(
    test_linode_client, test_volume_with_encryption
):
    volume = test_linode_client.load(Volume, test_volume_with_encryption.id)

    assert volume.id == test_volume_with_encryption.id
    assert volume.encryption == "enabled"


def test_update_volume_tag(test_linode_client, test_volume):
    volume = test_volume
    tag_1 = get_test_label(10)
    tag_2 = get_test_label(10)

    volume.tags = [tag_1, tag_2]
    volume.save()

    volume = test_linode_client.load(Volume, test_volume.id)

    assert all(tag in volume.tags for tag in [tag_1, tag_2])


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

    res = retry_sending_request(5, volume.attach, linode.id, backoff=30)

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


def test_volume_types(test_linode_client):
    types = test_linode_client.volumes.types()

    if len(types) > 0:
        for volume_type in types:
            assert type(volume_type) is VolumeType
            assert volume_type.price.monthly is None or (
                isinstance(volume_type.price.monthly, (float, int))
                and volume_type.price.monthly >= 0
            )
            if len(volume_type.region_prices) > 0:
                region_price = volume_type.region_prices[0]
                assert type(region_price) is RegionPrice
                assert region_price.monthly is None or (
                    isinstance(region_price.monthly, (float, int))
                    and region_price.monthly >= 0
                )

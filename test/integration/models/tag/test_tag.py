from test.integration.helpers import get_test_label

import pytest

from linode_api4.objects import ReservedIPAddress, Tag


@pytest.fixture
def test_tag(test_linode_client):
    unique_tag = get_test_label() + "_tag"
    tag = test_linode_client.tag_create(unique_tag)

    yield tag

    tag.delete()


@pytest.fixture
def create_tag_with_reserved_ip(test_linode_client, create_reserved_ip):
    unique_tag = get_test_label() + "_tag"
    reserved_ip = create_reserved_ip

    tag = test_linode_client.tags.create(
        unique_tag, reserved_ipv4_addresses=[reserved_ip.address]
    )
    reserved_ip = test_linode_client.networking.reserved_ips(
        ReservedIPAddress.address == reserved_ip.address
    )[0]

    yield tag, reserved_ip

    tag.delete()


@pytest.mark.smoke
def test_get_tag(test_linode_client, test_tag):
    tag = test_linode_client.load(Tag, test_tag.id)

    assert tag.id == test_tag.id


def test_get_tag_with_reserved_ip(
    test_linode_client, create_tag_with_reserved_ip
):
    tag, reserved_ip = create_tag_with_reserved_ip
    tag = test_linode_client.load(Tag, tag.id).objects[0]

    assert vars(tag).keys() == vars(reserved_ip).keys()
    assert tag.address == reserved_ip.address
    assert tag.reserved == reserved_ip.reserved
    assert tag.tags == reserved_ip.tags

    tag.delete()
    reserved_ip = test_linode_client.networking.reserved_ips(
        ReservedIPAddress.address == reserved_ip.address
    )
    assert len(reserved_ip) == 0

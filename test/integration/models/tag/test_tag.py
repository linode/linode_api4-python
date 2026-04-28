from test.integration.helpers import get_test_label

import pytest

from linode_api4.objects import Tag


@pytest.fixture
def test_tag(test_linode_client):
    unique_tag = get_test_label() + "_tag"
    tag = test_linode_client.tag_create(unique_tag)

    yield tag

    tag.delete()


@pytest.mark.smoke
def test_get_tag(test_linode_client, test_tag):
    tag = test_linode_client.load(Tag, test_tag.id)

    assert tag.id == test_tag.id


@pytest.mark.skip(reason="This test is currently blocked - API does not support tagging reserved IPs yet")
def test_get_tag_with_reserved_ip(test_linode_client, create_reserved_ip):
    unique_tag = get_test_label() + "_tag"
    reserved_ip = create_reserved_ip

    tag = test_linode_client.tags.create(unique_tag, reserved_ipv4_addresses=[reserved_ip.address])
    tag = test_linode_client.load(Tag, tag.id)
    assert tag.type == "reserved_ipv4_address"
    # assert tag.data...

    tag.delete()

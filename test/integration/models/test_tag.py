from test.integration.helpers import get_test_label

import pytest

from linode_api4.objects import Instance, Tag


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

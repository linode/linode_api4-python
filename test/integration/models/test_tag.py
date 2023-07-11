from test.integration.helpers import get_test_label

import pytest

from linode_api4.objects import Instance, Tag


@pytest.fixture
def create_tag(get_client):
    unique_tag = get_test_label() + "_tag"
    tag = get_client.tag_create(unique_tag)

    yield tag

    tag.delete()


@pytest.mark.smoke
def test_get_tag(get_client, create_tag):
    tag = get_client.load(Tag, create_tag.id)

    assert tag.id == create_tag.id

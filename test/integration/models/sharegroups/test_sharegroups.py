import datetime

from test.integration.helpers import (
    get_test_label,
)

import pytest

from linode_api4.objects import (
    Image,
    ImageShareGroup,
    ImageShareGroupMemberToAdd,
    ImageShareGroupToken,
)


def wait_for_image_status(test_linode_client, image_id, expected_status, timeout=180, interval=5):
    import time

    get_image = test_linode_client.load(Image, image_id)
    timer = 0
    while get_image.status != expected_status and timer < timeout:
        time.sleep(interval)
        timer += interval
        get_image = test_linode_client.load(Image, image_id)
    if timer >= timeout:
        raise TimeoutError(
            f"Created image did not reach status '{expected_status}' within {timeout} seconds."
        )


@pytest.fixture(scope="function")
def create_image_id(test_linode_client, linode_for_legacy_interface_tests):
    # TODO: list disks by linode_for_legacy_interface_tests.id
    create_image = test_linode_client.images.create(disks[0], label="linode-api4python-test-image-sharing-image")
    wait_for_image_status(test_linode_client, create_image.id, "available")
    yield create_image.id


@pytest.fixture(scope="function")
def share_group_id(test_linode_client):
    group_label = get_test_label(8) + "_sharegroup_api4_test"
    response = test_linode_client.sharegroups.create_sharegroup(
        label=group_label,
        description="Test api4python",
    )
    yield response.id


def test_get_share_groups(test_linode_client):
    response = test_linode_client.sharegroups()
    sharegroups_list = response.lists[0]
    assert len(sharegroups_list) > 0
    assert sharegroups_list[0].api_endpoint == '/images/sharegroups/{id}'
    assert sharegroups_list[0].id > 0
    assert sharegroups_list[0].description != ''
    assert isinstance(sharegroups_list[0].images_count, int)
    assert sharegroups_list[0].is_suspended == False
    assert sharegroups_list[0].label != ''
    assert isinstance(sharegroups_list[0].members_count, int)
    assert sharegroups_list[0].uuid != ''
    assert isinstance(sharegroups_list[0].created, datetime.date)
    assert isinstance(sharegroups_list[0].updated, datetime.date)
    assert not sharegroups_list[0].expiry


def test_add_update_remove_share_group(test_linode_client):
    group_label = get_test_label(8) + "_sharegroup_api4_test"
    response_create = test_linode_client.sharegroups.create_sharegroup(
        label=group_label,
        description="Test api4python create",
    )
    assert response_create.api_endpoint == '/images/sharegroups/{id}'
    assert response_create.id > 0
    assert response_create.description == 'Test api4python create'
    assert isinstance(response_create.images_count, int)
    assert response_create.is_suspended == False
    assert response_create.label == group_label
    assert isinstance(response_create.members_count, int)
    assert response_create.uuid != ''
    assert isinstance(response_create.created, datetime.date)
    assert not response_create.updated
    assert not response_create.expiry

    # TODO: update sharegroup label or description

    response_get = test_linode_client.load(ImageShareGroup, response_create.id)
    assert response_get.id == response_create.id
    assert response_get.description == 'Test api4python create'

    response_create.delete()
    with pytest.raises(RuntimeError) as err:
        test_linode_client.load(ImageShareGroup, response_create.id)
    assert "[404] Not found" in str(err.value)


def test_create_and_list_share_groups_by_image_id(test_linode_client, create_image_id):
    group_label = get_test_label(8) + "_sharegroup_api4_test"
    response_create_share_group = test_linode_client.sharegroups.create_sharegroup(
        label=group_label,
        description="Test api4python create",
    )

    response_create_share_group.sharegroups_by_image_id(image_id=create_image_id)
    # TODO: Add assertions

    response_create_share_group.delete()


def test_list_tokens(test_linode_client):
    response = test_linode_client.sharegroups.tokens()
    assert response.page_endpoint == 'images/sharegroups/tokens'
    assert len(response.lists[0]) >= 0


def test_create_token_to_own_share_group_error(test_linode_client):
    group_label = get_test_label(8) + "_sharegroup_api4_test"
    response_create_share_group = test_linode_client.sharegroups.create_sharegroup(
        label=group_label,
        description="Test api4python create",
    )
    with pytest.raises(RuntimeError) as err:
        test_linode_client.sharegroups.create_token(response_create_share_group.uuid)
    assert "[400] valid_for_sharegroup_uuid" in str(err.value)
    assert "You may not create a token for your own sharegroup" in str(err.value)

    response_create_share_group.delete()


def test_get_invalid_token(test_linode_client):
    with pytest.raises(RuntimeError) as err:
        test_linode_client.load(ImageShareGroupToken, "36b0-4d52_invalid")
    assert "[404] Not found" in str(err.value)


def test_try_to_add_member_invalid_token(test_linode_client, share_group_id):
    share_group = test_linode_client.load(ImageShareGroup, share_group_id)
    with pytest.raises(RuntimeError) as err:
        share_group.add_member(
            ImageShareGroupMemberToAdd(
                token="notExistingToken",
                label="New Member",
            )
        )
    assert "[500] Invalid token format" in str(err.value)
    share_group.delete()


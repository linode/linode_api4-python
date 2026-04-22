import datetime
from test.integration.conftest import get_region
from test.integration.helpers import (
    get_test_label,
)

import pytest

from linode_api4.objects import (
    Image,
    ImageShareGroup,
    ImageShareGroupImagesToAdd,
    ImageShareGroupImageToAdd,
    ImageShareGroupImageToUpdate,
    ImageShareGroupMemberToAdd,
    ImageShareGroupMemberToUpdate,
    ImageShareGroupToken,
)


def wait_for_image_status(
    test_linode_client, image_id, expected_status, timeout=360, interval=5
):
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


@pytest.fixture(scope="class")
def sample_linode(test_linode_client, e2e_test_firewall):
    client = test_linode_client
    region = get_region(client, {"Linodes", "Cloud Firewall"}, site_type="core")
    label = get_test_label(length=8)

    linode_instance = client.linode.instance_create(
        "g6-nanode-1",
        region,
        image="linode/alpine3.19",
        label=label + "_modlinode",
        root_pass="aComplex@Password123",
    )
    yield linode_instance
    linode_instance.delete()


@pytest.fixture(scope="class")
def create_image_id(test_linode_client, sample_linode):
    create_image = test_linode_client.images.create(
        sample_linode.disks[0],
        label="linode-api4python-test-image-sharing-image",
    )
    wait_for_image_status(test_linode_client, create_image.id, "available")
    yield create_image.id
    create_image.delete()


@pytest.fixture(scope="function")
def share_group_id(test_linode_client):
    group_label = get_test_label(8) + "_sharegroup_api4_test"
    group = test_linode_client.sharegroups.create_sharegroup(
        label=group_label,
        description="Test api4python",
    )
    yield group.id
    group.delete()


def test_get_share_groups(test_linode_client, share_group_id):
    response = test_linode_client.sharegroups()
    sharegroups_list = response.lists[0]
    assert len(sharegroups_list) > 0
    assert sharegroups_list[0].api_endpoint == "/images/sharegroups/{id}"
    assert sharegroups_list[0].id > 0
    assert sharegroups_list[0].description != ""
    assert isinstance(sharegroups_list[0].images_count, int)
    assert not sharegroups_list[0].is_suspended
    assert sharegroups_list[0].label != ""
    assert isinstance(sharegroups_list[0].members_count, int)
    assert sharegroups_list[0].uuid != ""
    assert isinstance(sharegroups_list[0].created, datetime.date)
    assert not sharegroups_list[0].expiry


def test_add_update_remove_share_group(test_linode_client):
    group_label = get_test_label(8) + "_sharegroup_api4_test"
    share_group = test_linode_client.sharegroups.create_sharegroup(
        label=group_label,
        description="Test api4python create",
    )
    assert share_group.api_endpoint == "/images/sharegroups/{id}"
    assert share_group.id > 0
    assert share_group.description == "Test api4python create"
    assert isinstance(share_group.images_count, int)
    assert not share_group.is_suspended
    assert share_group.label == group_label
    assert isinstance(share_group.members_count, int)
    assert share_group.uuid != ""
    assert isinstance(share_group.created, datetime.date)
    assert not share_group.updated
    assert not share_group.expiry

    load_share_group = test_linode_client.load(ImageShareGroup, share_group.id)
    assert load_share_group.id == share_group.id
    assert load_share_group.description == "Test api4python create"

    load_share_group.label = "Updated Sharegroup Label"
    load_share_group.description = "Test update description"
    load_share_group.save()
    load_share_group_after_update = test_linode_client.load(
        ImageShareGroup, share_group.id
    )
    assert load_share_group_after_update.id == share_group.id
    assert load_share_group_after_update.label == "Updated Sharegroup Label"
    assert (
        load_share_group_after_update.description == "Test update description"
    )

    share_group.delete()
    with pytest.raises(RuntimeError) as err:
        test_linode_client.load(ImageShareGroup, share_group.id)
    assert "[404] Not found" in str(err.value)


def test_add_get_update_revoke_image_to_share_group(
    test_linode_client, create_image_id, share_group_id
):
    share_group = test_linode_client.load(ImageShareGroup, share_group_id)
    add_image_response = share_group.add_images(
        ImageShareGroupImagesToAdd(
            images=[
                ImageShareGroupImageToAdd(id=create_image_id),
            ]
        )
    )
    assert 0 < len(add_image_response)
    assert (
        add_image_response[0].image_sharing.shared_by.sharegroup_id
        == share_group.id
    )
    assert (
        add_image_response[0].image_sharing.shared_by.source_image_id
        == create_image_id
    )

    get_response = share_group.get_image_shares()
    assert 0 < len(get_response)
    assert (
        get_response[0].image_sharing.shared_by.sharegroup_id == share_group.id
    )
    assert (
        get_response[0].image_sharing.shared_by.source_image_id
        == create_image_id
    )
    assert get_response[0].description == ""

    update_response = share_group.update_image_share(
        ImageShareGroupImageToUpdate(
            image_share_id=get_response[0].id, description="Description update"
        )
    )
    assert update_response.description == "Description update"

    share_groups_by_image_id_response = (
        test_linode_client.sharegroups.sharegroups_by_image_id(create_image_id)
    )
    assert 0 < len(share_groups_by_image_id_response.lists)
    assert share_groups_by_image_id_response.lists[0][0].id == share_group.id

    share_group.revoke_image_share(get_response[0].id)
    get_after_revoke_response = share_group.get_image_shares()
    assert len(get_after_revoke_response) == 0


def test_list_tokens(test_linode_client):
    response = test_linode_client.sharegroups.tokens()
    assert response.page_endpoint == "images/sharegroups/tokens"
    assert len(response.lists[0]) >= 0


def test_create_token_to_own_share_group_error(test_linode_client):
    group_label = get_test_label(8) + "_sharegroup_api4_test"
    response_create_share_group = (
        test_linode_client.sharegroups.create_sharegroup(
            label=group_label,
            description="Test api4python create",
        )
    )
    with pytest.raises(RuntimeError) as err:
        test_linode_client.sharegroups.create_token(
            response_create_share_group.uuid
        )
    assert "[400] valid_for_sharegroup_uuid" in str(err.value)
    assert "You may not create a token for your own sharegroup" in str(
        err.value
    )

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
                token="not_existing_token",
                label="New Member",
            )
        )
    assert "[500] Invalid token format" in str(err.value)


def test_list_share_group_members(test_linode_client, share_group_id):
    share_group = test_linode_client.load(ImageShareGroup, share_group_id)
    response = share_group.get_members()
    assert 0 == len(response)


def test_try_to_get_update_revoke_share_group_member_by_invalid_token(
    test_linode_client, share_group_id
):
    share_group = test_linode_client.load(ImageShareGroup, share_group_id)
    with pytest.raises(RuntimeError) as err:
        share_group.get_member("not_existing_token")
    assert "[404] Not found" in str(err.value)

    with pytest.raises(RuntimeError) as err:
        share_group.update_member(
            ImageShareGroupMemberToUpdate(
                token_uuid="not_existing_token",
                label="Update Member",
            )
        )
    assert "[404] Not found" in str(err.value)

    with pytest.raises(RuntimeError) as err:
        share_group.remove_member("not_existing_token")
    assert "[404] Not found" in str(err.value)

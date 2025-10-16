import pytest

from linode_api4.objects import EntityAccess, LinodeEntity


@pytest.mark.smoke
def test_get_role_permissions(test_linode_client):
    client = test_linode_client
    iam = client.iam

    permissions = iam.role_permissions()

    assert "account_access" in permissions
    assert isinstance(permissions["account_access"], list)


@pytest.mark.smoke
def test_get_user_role_permissions(test_linode_client):
    client = test_linode_client
    iam = client.iam

    username = client.profile().username
    user_permissions = iam.role_permissions_user_get(username)

    assert "account_access" in user_permissions
    assert isinstance(user_permissions["account_access"], list)


@pytest.mark.skip(
    reason="Updating IAM role permissions may require elevated privileges."
)
def test_set_user_role_permissions(test_linode_client):
    client = test_linode_client
    iam = client.iam

    username = client.profile().username
    entity_access = [EntityAccess(id=1, type="linode", roles=["read_only"])]

    updated = iam.role_permissions_user_set(
        username,
        account_access=["read_only"],
        entity_access=entity_access,
    )

    assert "account_access" in updated
    assert "entity_access" in updated


@pytest.mark.smoke
def test_list_entities(test_linode_client):
    client = test_linode_client
    iam = client.iam

    entities = iam.entities()

    if len(entities) > 0:
        entity = entities[0]
        assert isinstance(entity, LinodeEntity)
        assert hasattr(entity, "id")
        assert hasattr(entity, "label")
        assert hasattr(entity, "type")
    else:
        pytest.skip("No entities found in IAM response.")

import pytest

from linode_api4.objects import EntityAccess, LinodeEntity


def test_get_role_permissions(test_linode_client):
    client = test_linode_client
    iam = client.iam

    permissions = iam.role_permissions()

    assert "account_access" in permissions
    assert isinstance(permissions["account_access"], list)


def test_get_user_role_permissions(test_linode_client):
    client = test_linode_client
    iam = client.iam

    username = client.profile().username
    user_permissions = iam.role_permissions_user_get(username)

    assert "account_access" in user_permissions
    assert isinstance(user_permissions["account_access"], list)


def test_set_user_role_permissions(test_linode_client, test_firewall):
    client = test_linode_client
    firewall_id = test_firewall.id

    username = client.profile().username
    user_permissions = client.iam.role_permissions_user_get(username)["account_access"]
    entity_access = EntityAccess(id=firewall_id, type="firewall", roles=["firewall_admin"]).dict

    updated_perms = client.iam.role_permissions_user_set(
        username,
        account_access=user_permissions,
        entity_access=[entity_access],
    )

    assert "account_access" in updated_perms
    assert updated_perms["entity_access"][0]["id"] == firewall_id
    assert updated_perms["entity_access"][0]["roles"] == ["firewall_admin"]
    assert updated_perms["entity_access"][0]["type"] == "firewall"


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


def test_get_account_permissions(test_linode_client):
    client = test_linode_client
    username = client.profile().username

    account_permissions = client.iam.account_permissions_get(username)

    if not account_permissions:
        pytest.fail("No account permissions found for the user.")
    else:
        assert len(account_permissions) > 0


def test_get_entity_permissions(test_linode_client):
    client = test_linode_client
    username = client.profile().username

    entities = client.iam.entities()
    if not entities:
        pytest.fail("No entities found in IAM response.")
    else:
        entity = entities[0]
        entity_permissions = client.iam.entity_permissions_get(
            username, entity.type, entity.id
        )
        if not entity_permissions:
            pytest.fail(
                "No entity permissions found for the user and chosen entity."
            )
        else:
            assert len(entity_permissions) > 0

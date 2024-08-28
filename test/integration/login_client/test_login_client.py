import pytest

from linode_api4 import OAuthScopes
from linode_api4.login_client import LinodeLoginClient
from linode_api4.objects import OAuthClient


@pytest.fixture
def linode_login_client(test_oauth_client):
    client_id = test_oauth_client.id
    client_secret = test_oauth_client.secret

    login_client = LinodeLoginClient(client_id, client_secret)

    yield login_client


@pytest.fixture
def test_oauth_client_two(test_linode_client):
    client = test_linode_client
    oauth_client = client.account.oauth_client_create(
        "test-oauth-client-two", "https://localhost/oauth/callback"
    )

    yield oauth_client

    oauth_client.delete()


@pytest.mark.smoke
def test_get_oathclient(test_linode_client, test_oauth_client):
    client = test_linode_client

    oauth_client = client.load(OAuthClient, test_oauth_client.id)

    assert "_oauth" in test_oauth_client.label
    assert "https://localhost/oauth/callback" == oauth_client.redirect_uri


def test_get_oauth_clients(
    test_linode_client, test_oauth_client, test_oauth_client_two
):
    oauth_clients = test_linode_client.account.oauth_clients()

    id_list = [o_cli.id for o_cli in oauth_clients]

    assert str(test_oauth_client.id) in id_list
    assert str(test_oauth_client_two.id) in id_list


def test_get_oauth_clients_dont_reveal_secret(
    test_linode_client, test_oauth_client
):
    oauth_client_secret = test_linode_client.account.oauth_clients()[0].secret

    assert oauth_client_secret == "<REDACTED>"


def test_edit_oauth_client_details(test_linode_client, test_oauth_client_two):
    test_oauth_client_two.redirect_uri = (
        "https://localhost/oauth/callback_changed"
    )
    test_oauth_client_two.label = "new_oauthclient_label"
    test_oauth_client_two.save()

    oau_client = test_linode_client.load(OAuthClient, test_oauth_client_two.id)

    assert oau_client.redirect_uri == "https://localhost/oauth/callback_changed"
    assert oau_client.label == "new_oauthclient_label"


def test_oauth_client_reset_secrets(test_oauth_client_two):
    old_secret = test_oauth_client_two.secret

    new_secret = test_oauth_client_two.reset_secret()

    assert old_secret != new_secret


def test_linode_login_client_generate_default_login_url(linode_login_client):
    client_id = linode_login_client.client_id
    url = linode_login_client.generate_login_url()

    assert (
        "https://login.linode.com/oauth/authorize?client_id="
        + str(client_id)
        + "&response_type=code"
        == url
    )


def test_linode_login_client_generate_login_url_with_scope(linode_login_client):
    url = linode_login_client.generate_login_url(
        scopes=OAuthScopes.Linodes.read_write
    )

    assert "scopes=linodes%3Aread_write" in url


def test_linode_login_client_expire_token(
    linode_login_client, test_oauth_client
):
    result = linode_login_client.expire_token(token=test_oauth_client.secret)

    assert result is True

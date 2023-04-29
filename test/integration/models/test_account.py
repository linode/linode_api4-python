import time
from test.integration.helpers import get_test_label

from linode_api4.objects import (
    Account,
    AccountSettings,
    Event,
    Login,
    OAuthClient,
    User,
)


def test_get_account(get_client):
    client = get_client
    account = client.load(Account(client, "test-123@linode.com"))

    assert account.first_name == "Test"
    assert account.last_name == "User"
    assert account.email == "test-123@linode.com"
    assert account.phone == "111-111-1111"
    assert account.address_1 == "3rd & Arch St"
    assert account.address_2 == "Unit 999"
    assert account.city == "Philadelphia"
    assert account.state == "PA"
    assert account.country == "US"
    assert account.zip == "19106"
    assert account.tax_id == "999-99-9999"


def test_get_login(get_client):
    client = get_client
    login = client.load(Login(client, "", {}), "")

    updated_time = int(time.mktime(getattr(login, "_last_updated").timetuple()))

    login_updated = int(time.time()) - updated_time

    assert "username" in str(login._raw_json)
    assert "ip" in str(login._raw_json)
    assert "datetime" in str(login._raw_json)
    assert "status" in str(login._raw_json)
    assert login_updated < 15


def test_get_account_settings(get_client):
    client = get_client
    account_settings = client.load(AccountSettings(client, ""), "")

    assert "managed" in str(account_settings._raw_json)
    assert "network_helper" in str(account_settings._raw_json)
    assert "longview_subscription" in str(account_settings._raw_json)
    assert "backups_enabled" in str(account_settings._raw_json)
    assert "object_storage" in str(account_settings._raw_json)


def test_latest_get_event(get_client):
    client = get_client

    available_regions = client.regions()
    chosen_region = available_regions[0]
    label = get_test_label()

    linode, password = client.linode.instance_create(
        "g5-standard-4", chosen_region, image="linode/debian9", label=label
    )

    events = client.load(Event, "")

    latest_event = events._raw_json.get("data")[0]

    linode.delete()

    assert "linode_" in latest_event
    assert label in latest_event


def test_get_oathclient(get_client, create_oauth_client):
    client = get_client

    oauth_client = client.load(OAuthClient, create_oauth_client.id)

    assert "test-oauth-client" == oauth_client.label
    assert "https://localhost/oauth/callback" == oauth_client.redirect_uri


def test_get_user(get_client):
    client = get_client

    events = client.load(Event, "")

    username = events._raw_json.get("data")[0]["username"]

    user = client.laod(User, username)

    assert username == user.username
    assert "email" in user._raw_json
    assert "email" in user._raw_json

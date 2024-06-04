import time
from test.integration.helpers import get_test_label

import pytest

from linode_api4.objects import (
    Account,
    AccountSettings,
    ChildAccount,
    Event,
    Login,
    User,
)


@pytest.mark.smoke
def test_get_account(test_linode_client):
    client = test_linode_client
    account = client.account()
    account_id = account.id
    account_get = client.load(Account, account_id)

    assert account_get.first_name == account.first_name
    assert account_get.last_name == account.last_name
    assert account_get.email == account.email
    assert account_get.phone == account.phone
    assert account_get.address_1 == account.address_1
    assert account_get.address_2 == account.address_2
    assert account_get.city == account.city
    assert account_get.state == account.state
    assert account_get.country == account.country
    assert account_get.zip == account.zip
    assert account_get.tax_id == account.tax_id


def test_get_login(test_linode_client):
    client = test_linode_client
    login = client.load(Login(client, "", {}), "")

    updated_time = int(time.mktime(getattr(login, "_last_updated").timetuple()))

    login_updated = int(time.time()) - updated_time

    assert "username" in str(login._raw_json)
    assert "ip" in str(login._raw_json)
    assert "datetime" in str(login._raw_json)
    assert "status" in str(login._raw_json)
    assert login_updated < 15


def test_get_account_settings(test_linode_client):
    client = test_linode_client
    account_settings = client.load(AccountSettings(client, ""), "")

    assert "managed" in str(account_settings._raw_json)
    assert "network_helper" in str(account_settings._raw_json)
    assert "longview_subscription" in str(account_settings._raw_json)
    assert "backups_enabled" in str(account_settings._raw_json)
    assert "object_storage" in str(account_settings._raw_json)


@pytest.mark.smoke
def test_latest_get_event(test_linode_client):
    client = test_linode_client

    available_regions = client.regions()
    chosen_region = available_regions[4]
    label = get_test_label()

    linode, password = client.linode.instance_create(
        "g6-nanode-1", chosen_region, image="linode/debian10", label=label
    )

    events = client.load(Event, "")

    latest_event = events._raw_json.get("data")[0]

    linode.delete()

    assert label in latest_event["entity"]["label"]


def test_get_user(test_linode_client):
    client = test_linode_client

    events = client.load(Event, "")

    username = events._raw_json.get("data")[0]["username"]

    user = client.load(User, username)

    assert username == user.username
    assert "email" in user._raw_json
    assert "email" in user._raw_json


def test_list_child_accounts(test_linode_client):
    pytest.skip("Configure test account settings for Parent child")
    client = test_linode_client
    child_accounts = client.account.child_accounts()
    if len(child_accounts) > 0:
        child_account = ChildAccount(client, child_accounts[0].euuid)
        child_account._api_get()
        child_account.create_token()

import time
from datetime import datetime
from test.integration.conftest import get_region
from test.integration.helpers import get_test_label, retry_sending_request

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
    login = retry_sending_request(3, client.load, Login(client, "", {}), "")

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
    assert isinstance(account_settings.interfaces_for_new_linodes, str)
    assert "maintenance_policy" in str(account_settings._raw_json)


def test_update_maintenance_policy(test_linode_client):
    client = test_linode_client
    settings = client.load(AccountSettings(client, ""), "")

    original_policy = settings.maintenance_policy
    new_policy = (
        "linode/power_off_on"
        if original_policy == "linode/migrate"
        else "linode/migrate"
    )

    settings.maintenance_policy = new_policy
    settings.save()

    updated = client.load(AccountSettings(client, ""), "")
    assert updated.maintenance_policy == new_policy

    settings.maintenance_policy = original_policy
    settings.save()

    updated = client.load(AccountSettings(client, ""), "")
    assert updated.maintenance_policy == original_policy


@pytest.mark.smoke
def test_latest_get_event(test_linode_client, e2e_test_firewall):
    client = test_linode_client

    region = get_region(client, {"Linodes", "Cloud Firewall"}, site_type="core")
    label = get_test_label()

    linode, password = client.linode.instance_create(
        "g6-nanode-1",
        region,
        image="linode/debian12",
        label=label,
        firewall=e2e_test_firewall,
    )

    events = client.load(Event, "")

    latest_events = events._raw_json.get("data")

    linode.delete()

    for event in latest_events[:15]:
        if label == event["entity"]["label"]:
            break
    else:
        assert False, f"Linode '{label}' not found in the last 15 events"


def test_get_user(test_linode_client):
    client = test_linode_client

    events = client.load(Event, "")

    username = events._raw_json.get("data")[0]["username"]

    user = client.load(User, username)

    assert username == user.username
    assert "email" in user._raw_json


def test_list_child_accounts(test_linode_client):
    pytest.skip("Configure test account settings for Parent child")
    client = test_linode_client
    child_accounts = client.account.child_accounts()
    if len(child_accounts) > 0:
        child_account = ChildAccount(client, child_accounts[0].euuid)
        child_account._api_get()
        child_account.create_token()


def test_get_invoice(test_linode_client):
    client = test_linode_client

    invoices = client.account.invoices()

    if len(invoices) > 0:
        assert isinstance(invoices[0].subtotal, float)
        assert isinstance(invoices[0].tax, float)
        assert isinstance(invoices[0].total, float)
        assert r"'billing_source': 'linode'" in str(invoices[0]._raw_json)


def test_get_payments(test_linode_client):
    client = test_linode_client

    payments = client.account.payments()

    if len(payments) > 0:
        assert isinstance(payments[0].date, datetime)
        assert isinstance(payments[0].usd, float)

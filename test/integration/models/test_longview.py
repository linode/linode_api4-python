import re
import time

import pytest

from linode_api4.objects import LongviewClient, LongviewSubscription


@pytest.mark.smoke
def test_get_longview_client(test_linode_client, test_longview_client):
    longview = test_linode_client.load(LongviewClient, test_longview_client.id)

    assert longview.id == test_longview_client.id


def test_update_longview_label(test_linode_client, test_longview_client):
    longview = test_linode_client.load(LongviewClient, test_longview_client.id)
    old_label = longview.label

    label = "updated_longview_label"

    longview.label = label

    longview.save()

    assert longview.label != old_label


def test_delete_client(test_linode_client, test_longview_client):
    client = test_linode_client
    label = "TestSDK-longview"
    longview_client = client.longview.client_create(label=label)

    time.sleep(5)

    res = longview_client.delete()

    assert res


def test_get_longview_subscription(test_linode_client, test_longview_client):
    subs = test_linode_client.longview.subscriptions()
    sub = test_linode_client.load(LongviewSubscription, subs[0].id)

    assert "clients_included" in str(subs.first().__dict__)

    assert re.search("[0-9]+", str(sub.price.hourly))
    assert re.search("[0-9]+", str(sub.price.monthly))

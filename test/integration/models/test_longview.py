import re
import time

import pytest

from linode_api4.objects import LongviewClient, LongviewSubscription


@pytest.mark.smoke
def test_get_longview_client(get_client, create_longview_client):
    longview = get_client.load(LongviewClient, create_longview_client.id)

    assert longview.id == create_longview_client.id


def test_update_longview_label(get_client, create_longview_client):
    longview = get_client.load(LongviewClient, create_longview_client.id)
    old_label = longview.label

    label = "updated_longview_label"

    longview.label = label

    longview.save()

    assert longview.label != old_label


def test_delete_client(get_client, create_longview_client):
    client = get_client
    label = "TestSDK-longview"
    longview_client = client.longview.client_create(label=label)

    time.sleep(5)

    res = longview_client.delete()

    assert res


def test_get_longview_subscription(get_client, create_longview_client):
    subs = get_client.longview.subscriptions()
    sub = get_client.load(LongviewSubscription, subs[0].id)

    assert "clients_included" in str(subs.first().__dict__)

    assert re.search("[0-9]+", str(sub.price.hourly))
    assert re.search("[0-9]+", str(sub.price.monthly))

import re
import time
from test.integration.helpers import get_test_label

import pytest

from linode_api4.objects import (
    ApiError,
    LongviewClient,
    LongviewPlan,
    LongviewSubscription,
)


@pytest.mark.smoke
def test_get_longview_client(test_linode_client, test_longview_client):
    longview = test_linode_client.load(LongviewClient, test_longview_client.id)

    assert longview.id == test_longview_client.id


def test_update_longview_label(test_linode_client, test_longview_client):
    longview = test_linode_client.load(LongviewClient, test_longview_client.id)
    old_label = longview.label

    label = get_test_label(10)

    longview.label = label

    longview.save()

    assert longview.label != old_label


def test_delete_client(test_linode_client, test_longview_client):
    client = test_linode_client
    label = get_test_label(length=8)
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

    assert "longview-3" in str(subs.lists)
    assert "longview-10" in str(subs.lists)
    assert "longview-40" in str(subs.lists)
    assert "longview-100" in str(subs.lists)


def test_longview_plan_update_method_not_allowed(test_linode_client):
    try:
        test_linode_client.longview.longview_plan_update("longview-100")
    except ApiError as e:
        assert e.status == 405
        assert "Method Not Allowed" in str(e)


def test_get_current_longview_plan(test_linode_client):
    lv_plan = test_linode_client.load(LongviewPlan, "")

    if lv_plan.label is not None:
        assert "Longview" in lv_plan.label
        assert "hourly" in lv_plan.price.dict
        assert "monthly" in lv_plan.price.dict

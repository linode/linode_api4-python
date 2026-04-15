import urllib.request

import pytest
from linode_api4 import LinodeClient, PaginatedList
from linode_api4.objects import (ObjectStorageACL,
                                 ObjectStorageKeys,
                                 ObjectStorageBucket)
from linode_api4.objects.monitor import (
    LogsDestination,
)
from test.integration.helpers import (
    get_test_label,
    send_request_when_resource_available,
    wait_for_condition,
)


@pytest.fixture(scope="session")
def test_object_storage_key(test_linode_client: LinodeClient):
    key = test_linode_client.object_storage.keys_create(
        label=get_test_label(),
    )
    yield key
    key.delete()


@pytest.fixture(scope="session")
def test_destination(
        test_linode_client: LinodeClient,
        test_object_storage_key: ObjectStorageKeys,
):
    bucket = test_linode_client.object_storage.bucket_create(
        cluster_or_region="us-southeast",
        label=get_test_label(),
        acl=ObjectStorageACL.PRIVATE,
        cors_enabled=False,
    )

    dest = test_linode_client.monitor.destination_create(
        label=get_test_label(),
        type="akamai_object_storage",
        access_key_id=test_object_storage_key.access_key,
        access_key_secret=test_object_storage_key.secret_key,
        bucket_name=bucket.label,
        host=f"{bucket.label}.us-southeast-1.linodeobjects.com",
    )

    yield dest

    send_request_when_resource_available(timeout=100, func=dest.delete)
    _empty_bucket(test_linode_client, bucket)
    send_request_when_resource_available(timeout=100, func=bucket.delete)


def _empty_bucket(client: LinodeClient, bucket: ObjectStorageBucket):
    """
    Helper function clearing objects in the test bucket so it can be deleted.
    """
    for obj in bucket.contents():
        signed = client.object_storage.object_url_create(
            cluster_or_region_id=bucket.region,
            bucket=bucket.label,
            method="DELETE",
            name=obj.name,
        )
        urllib.request.urlopen(
            urllib.request.Request(signed.url, method="DELETE")
        )


def test_list_destinations(test_linode_client: LinodeClient, test_destination: LogsDestination):
    """
    Test that listing destinations returns a PaginatedList containing the previously created destination.
    """
    destinations = test_linode_client.monitor.destinations()

    assert isinstance(destinations, PaginatedList)
    assert len(destinations) > 0
    assert all(isinstance(d, LogsDestination) for d in destinations)

    ids = [d.id for d in destinations]
    assert test_destination.id in ids


def test_get_destination_by_id(test_linode_client: LinodeClient, test_destination: LogsDestination):
    """
    Test that fetching destination with id filter returns correct destination.
    """
    destination_by_id = test_linode_client.load(LogsDestination, test_destination.id)

    assert isinstance(destination_by_id, LogsDestination)
    assert destination_by_id.id == test_destination.id
    assert destination_by_id.label == test_destination.label
    assert destination_by_id.type == test_destination.type


def test_update_destination_label(
        test_linode_client: LinodeClient,
        test_destination: LogsDestination,
        test_object_storage_key: ObjectStorageKeys,
):
    """
    Test that a LogsDestination label can be updated via save().
    """
    new_label = test_destination.label + "-upd"
    new_path = "updated/logs/path/"

    dest = test_linode_client.load(LogsDestination, test_destination.id)
    dest.label = new_label
    dest.details.path = new_path
    dest.details.access_key_secret = test_object_storage_key.secret_key
    dest.save()

    updated = test_linode_client.load(LogsDestination, test_destination.id)
    assert updated.label == new_label
    assert updated.details.path == new_path


def test_destination_history(test_linode_client: LinodeClient, test_destination: LogsDestination):
    """
    Test that LogsDestination.history returns version snapshots reflecting
    the state before and after the label/path update performed in test_update_mutable_fields.
    """
    dest = test_linode_client.load(LogsDestination, test_destination.id)
    history = dest.history

    assert history is not None
    assert len(history) >= 2

    snapshot_original = next(snap for snap in history if snap.version == 1)
    snapshot_updated = next(snap for snap in history if snap.version == 2)

    assert snapshot_updated.label == test_destination.label + "-upd"
    assert snapshot_updated.details.path == "updated/logs/path/"
    assert snapshot_updated.id == test_destination.id

    assert snapshot_original.label == test_destination.label
    assert snapshot_original.details.path == None
    assert snapshot_original.id == test_destination.id

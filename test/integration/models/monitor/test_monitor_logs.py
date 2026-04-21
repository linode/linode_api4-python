import urllib.request

import pytest
from linode_api4 import LinodeClient, PaginatedList
from linode_api4.objects import (ObjectStorageACL,
                                 ObjectStorageKeys,
                                 ObjectStorageBucket,
                                 Capability)
from linode_api4.objects.monitor import (
    LogsDestination,
)
from test.integration.helpers import (
    get_test_label,
    send_request_when_resource_available,
)


@pytest.fixture(scope="session", autouse=True)
def require_aclp_logs(test_linode_client: LinodeClient):
    """Skip all tests in this module if the aclp_logs feature is not enabled for the account."""
    account = test_linode_client.account()
    if Capability.aclp_logs not in account.capabilities:
        pytest.skip("aclp_logs feature is not enabled for this account")


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


def test_update_destination_label_and_version_history(
        test_linode_client: LinodeClient,
        test_destination: LogsDestination,
        test_object_storage_key: ObjectStorageKeys,
):
    """
    Test that a LogsDestination label can be updated via save(),
    and that history reflects both states.
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

    history = updated.history
    assert history is not None
    assert len(history) >= 2

    snapshot_original = next(snap for snap in history if snap.version == 1)
    snapshot_updated = next(snap for snap in history if snap.version == 2)

    assert snapshot_updated.label == new_label
    assert snapshot_updated.details.path == new_path
    assert snapshot_updated.id == test_destination.id

    assert snapshot_original.label == test_destination.label
    assert snapshot_original.details.path is None
    assert snapshot_original.id == test_destination.id


def test_fails_to_create_destination_invalid_secret(test_linode_client: LinodeClient):
    """
    Test that a destination create request with invalid access key results in a 400 ApiError.
    """
    from linode_api4.errors import ApiError

    with pytest.raises(ApiError) as excinfo:
        test_linode_client.monitor.destination_create(
            label=get_test_label(),
            type="akamai_object_storage",
            access_key_id="1",
            access_key_secret="1",
            bucket_name="some-bucket",
            host="some-bucket.us-southeast-1.linodeobjects.com",
        )
    assert excinfo.value.status == 400
    assert excinfo.value.errors == ['Invalid access key id or secret key']


def test_fails_to_create_destination_invalid_type(test_linode_client: LinodeClient):
    """
    Test that a destination create request with an unsupported type
    results in a 400 ApiError.
    """
    from linode_api4.errors import ApiError

    with pytest.raises(ApiError) as excinfo:
        test_linode_client.monitor.destination_create(
            label=get_test_label(),
            type="invalid_type",
            access_key_id="SOMEACCESSKEY",
            access_key_secret="SOMESECRETKEY",
            bucket_name="some-bucket",
            host="some-bucket.us-southeast-1.linodeobjects.com",
        )
    assert excinfo.value.status == 400
    assert excinfo.value.errors == ['Must be one of akamai_object_storage, custom_https']

def test_fails_to_create_destination_empty_required_fields(test_linode_client: LinodeClient):
    """
    Test that a destination create request with missing required fields
    results in a 400 ApiError.
    """
    from linode_api4.errors import ApiError

    with pytest.raises(ApiError) as excinfo:
        test_linode_client.monitor.destination_create(
            label=get_test_label(),
            type="akamai_object_storage",
            access_key_id="",
            access_key_secret="",
            bucket_name="",
            host="",
        )
    assert excinfo.value.status == 400
    assert len(excinfo.value.errors) == 4
    assert all(
        error == "Length must be 1-255 characters"
        for error in excinfo.value.errors
    )

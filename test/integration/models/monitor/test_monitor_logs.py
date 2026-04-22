import os
import urllib.request

import pytest

from linode_api4 import LinodeClient, PaginatedList, LogsStreamType
from linode_api4.objects import (ObjectStorageACL,
                                 ObjectStorageKeys,
                                 ObjectStorageBucket,
                                 Capability)
from linode_api4.objects.monitor import (
    LogsDestination,
    LogsStream,
    LogsStreamStatus,
)

from test.integration.helpers import (
    get_test_label,
    send_request_when_resource_available,
    wait_for_condition,
)

_RUN_ACLP_LOGS_STREAM_TESTS = "RUN_ACLP_LOGS_STREAM_TESTS"
_SKIP_STREAM_TESTS = pytest.mark.skipif(
    os.getenv(_RUN_ACLP_LOGS_STREAM_TESTS, "").strip().lower() not in {"yes", "true"},
    reason=f"{_RUN_ACLP_LOGS_STREAM_TESTS} environment variable must be set to 'yes' or 'true'",
)


@pytest.fixture(scope="session", autouse=True)
def require_aclp_logs(test_linode_client: LinodeClient):
    """Skip all tests in this module if the aclp_logs feature is not enabled for the account."""
    account = test_linode_client.account()
    if Capability.aclp_logs not in account.capabilities:
        pytest.skip("aclp_logs feature is not enabled for this account")


@pytest.fixture(scope="session")
def create_object_storage_key(test_linode_client: LinodeClient):
    key = test_linode_client.object_storage.keys_create(
        label=get_test_label(),
    )
    yield key
    key.delete()


@pytest.fixture(scope="session")
def test_destination(
        test_linode_client: LinodeClient,
        create_object_storage_key: ObjectStorageKeys,
):
    dest, bucket = _create_destination_with_bucket(test_linode_client, create_object_storage_key)
    yield dest
    _delete_destination_with_bucket(test_linode_client, dest, bucket)


def _create_destination_with_bucket(client: LinodeClient, key: ObjectStorageKeys):
    """Helper that creates an OBJ bucket and a logs destination backed by it."""
    bucket = client.object_storage.bucket_create(
        cluster_or_region="us-southeast",
        label=get_test_label(),
        acl=ObjectStorageACL.PRIVATE,
        cors_enabled=False,
    )
    dest = client.monitor.destination_create(
        label=get_test_label(),
        type="akamai_object_storage",
        access_key_id=key.access_key,
        access_key_secret=key.secret_key,
        bucket_name=bucket.label,
        host=f"{bucket.label}.us-southeast-1.linodeobjects.com",
    )
    return dest, bucket


def _delete_destination_with_bucket(client: LinodeClient, dest: LogsDestination, bucket: ObjectStorageBucket):
    """Helper that deletes a logs destination and its backing OBJ bucket."""
    send_request_when_resource_available(timeout=100, func=dest.delete)
    _empty_bucket(client, bucket)
    send_request_when_resource_available(timeout=100, func=bucket.delete)


def _skip_if_streams_exist(client: LinodeClient):
    """Skip the current test if any streams already exist on the account.
    Only one stream can be present per account at a time."""
    existing_streams = client.monitor.streams()
    if len(existing_streams) > 0:
        stream_labels = [s.label for s in existing_streams]
        pytest.skip(
            f"Skipping: existing stream(s) found on this account "
            f"(labels: {stream_labels}). Only one stream can be present per account."
        )


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
        create_object_storage_key: ObjectStorageKeys,
):
    """
    Test that a LogsDestination label can be updated via save(),
    and that history reflects both states.
    """
    new_label = test_destination.label + "-upd"
    new_path = "updated/logs/path/"

    dest = test_linode_client.load(LogsDestination, test_destination.id)
    original_version = dest.version
    dest.label = new_label
    dest.details.path = new_path
    dest.details.access_key_secret = create_object_storage_key.secret_key
    dest.save()

    updated = test_linode_client.load(LogsDestination, test_destination.id)
    assert updated.label == new_label
    assert updated.details.path == new_path

    history = updated.history
    assert history is not None
    assert len(history) >= 2

    snapshot_original = next(snap for snap in history if snap.version == original_version)
    snapshot_updated = next(snap for snap in history if snap.version == updated.version)

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


@_SKIP_STREAM_TESTS
def test_fails_to_create_stream_invalid_destination(test_linode_client: LinodeClient):
    """
    Test that creating a stream with a non-existent destination ID results in a 400 ApiError.
    Requires no other streams to be present on account. If a stream is already present test is skipped.
    """
    from linode_api4.errors import ApiError

    _skip_if_streams_exist(test_linode_client)

    with pytest.raises(ApiError) as excinfo:
        test_linode_client.monitor.stream_create(
            label=get_test_label(),
            type=LogsStreamType.audit_logs,
            destinations=[999999999],
        )
    assert excinfo.value.status == 400
    assert excinfo.value.errors == ['Destination not found']


@pytest.fixture(scope="session")
def create_secondary_destination(
        test_linode_client: LinodeClient,
        create_object_storage_key: ObjectStorageKeys,
):
    dest, bucket = _create_destination_with_bucket(test_linode_client, create_object_storage_key)
    yield dest
    _delete_destination_with_bucket(test_linode_client, dest, bucket)


@pytest.fixture(scope="session")
def create_stream(test_linode_client: LinodeClient, test_destination: LogsDestination):
    _skip_if_streams_exist(test_linode_client)

    stream = test_linode_client.monitor.stream_create(
        label=get_test_label(),
        destinations=[test_destination.id],
        type=LogsStreamType.audit_logs
    )
    assert stream.id is not None
    assert stream.status == LogsStreamStatus.provisioning
    yield stream
    send_request_when_resource_available(timeout=100, func=stream.delete)


@pytest.fixture(scope="session")
def provisioned_stream(test_linode_client: LinodeClient, create_stream: LogsStream):
    """
    Waits until the stream transitions out of provisioning state.
    NOTE: Stream provisioning can take up to 60 minutes to finish.
    """

    def is_stream_provisioned():
        stream = test_linode_client.load(LogsStream, create_stream.id)
        return stream.status in (LogsStreamStatus.active, LogsStreamStatus.inactive)

    wait_for_condition(60, 3600, is_stream_provisioned)

    yield test_linode_client.load(LogsStream, create_stream.id)


@_SKIP_STREAM_TESTS
def test_list_streams(test_linode_client: LinodeClient, provisioned_stream: LogsStream):
    """
    Test that listing streams returns a PaginatedList containing the previously created stream.
    """
    streams = test_linode_client.monitor.streams()

    assert isinstance(streams, PaginatedList)
    assert len(streams) > 0
    assert all(isinstance(s, LogsStream) for s in streams)

    ids = [s.id for s in streams]
    assert provisioned_stream.id in ids


@_SKIP_STREAM_TESTS
def test_get_stream_by_id(test_linode_client: LinodeClient, provisioned_stream: LogsStream):
    """
    Test that loading a stream by ID returns the correct stream with expected fields.
    """
    stream = test_linode_client.load(LogsStream, provisioned_stream.id)

    assert isinstance(stream, LogsStream)
    assert stream.id == provisioned_stream.id
    assert stream.label == provisioned_stream.label
    assert stream.status == provisioned_stream.status
    assert len(stream.destinations) == 1


@_SKIP_STREAM_TESTS
def test_update_stream_label_and_status(test_linode_client: LinodeClient, provisioned_stream: LogsStream):
    """
    Test that a LogsStream label and status can both be updated via save(), and that
    the version history reflects both the label and status changes across versions.
    """
    stream = test_linode_client.load(LogsStream, provisioned_stream.id)
    original_label = stream.label
    original_status = stream.status
    version_before = stream.version

    new_label = original_label + "-upd"
    new_status = (
        LogsStreamStatus.inactive
        if original_status == LogsStreamStatus.active
        else LogsStreamStatus.active
    )

    stream.label = new_label
    stream.status = new_status
    result = stream.save()
    assert result is True

    try:
        updated = test_linode_client.load(LogsStream, provisioned_stream.id)
        assert updated.label == new_label
        assert updated.status == new_status

        history = updated.history
        snapshot_original = next(h for h in history if h.version == version_before)
        snapshot_updated = next(h for h in history if h.version == updated.version)

        assert snapshot_original.label == original_label
        assert snapshot_original.status == original_status
        assert snapshot_updated.label == new_label
        assert snapshot_updated.status == new_status
        assert snapshot_updated.id == provisioned_stream.id
    finally:
        # Revert to original label and status
        stream.label = original_label
        stream.status = original_status
        stream.save()


@_SKIP_STREAM_TESTS
def test_update_stream_destinations(
        test_linode_client: LinodeClient,
        provisioned_stream: LogsStream,
        create_secondary_destination: LogsDestination,
):
    """
    Test that a stream destination can be replaced via update_destinations(),
    and that history reflects the change. The API allows exactly one destination per stream.
    """
    stream = test_linode_client.load(LogsStream, provisioned_stream.id)
    original_destinations = [stream.destinations[0].id]
    version_before = stream.version

    result = stream.update_destinations([create_secondary_destination.id])
    assert result is True

    try:
        updated = test_linode_client.load(LogsStream, provisioned_stream.id)
        assert len(updated.destinations) == 1
        assert updated.destinations[0].id == create_secondary_destination.id

        history = updated.history
        snapshot_original = next(h for h in history if h.version == version_before)
        snapshot_updated = next(h for h in history if h.version == updated.version)

        assert snapshot_original.destinations[0].id == original_destinations[0]
        assert snapshot_updated.destinations[0].id == create_secondary_destination.id
    finally:
        # Revert to original destination
        stream.update_destinations(original_destinations)

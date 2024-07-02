import time
from test.integration.conftest import get_region

import pytest

from linode_api4.linode_client import LinodeClient
from linode_api4.objects.object_storage import (
    ObjectStorageACL,
    ObjectStorageBucket,
    ObjectStorageKeyPermission,
    ObjectStorageKeys,
)


@pytest.fixture(scope="session")
def region(test_linode_client: LinodeClient):
    return get_region(test_linode_client, {"Object Storage"}).id


@pytest.fixture(scope="session")
def bucket(test_linode_client: LinodeClient, region: str):
    bucket = test_linode_client.object_storage.bucket_create(
        cluster_or_region=region,
        label="bucket-" + str(time.time_ns()),
        acl=ObjectStorageACL.PRIVATE,
        cors_enabled=False,
    )

    yield bucket
    bucket.delete()


@pytest.fixture(scope="session")
def obj_key(test_linode_client: LinodeClient):
    key = test_linode_client.object_storage.keys_create(
        label="obj-key-" + str(time.time_ns()),
    )

    yield key
    key.delete()


@pytest.fixture(scope="session")
def obj_limited_key(
    test_linode_client: LinodeClient, region: str, bucket: ObjectStorageBucket
):
    key = test_linode_client.object_storage.keys_create(
        label="obj-limited-key-" + str(time.time_ns()),
        bucket_access=test_linode_client.object_storage.bucket_access(
            cluster_or_region=region,
            bucket_name=bucket.label,
            permissions=ObjectStorageKeyPermission.READ_ONLY,
        ),
        regions=[region],
    )

    yield key
    key.delete()


def test_keys(
    test_linode_client: LinodeClient,
    obj_key: ObjectStorageKeys,
    obj_limited_key: ObjectStorageKeys,
):
    loaded_key = test_linode_client.load(ObjectStorageKeys, obj_key.id)
    loaded_limited_key = test_linode_client.load(
        ObjectStorageKeys, obj_limited_key.id
    )

    assert loaded_key.label == obj_key.label
    assert loaded_limited_key.label == obj_limited_key.label


def test_bucket(
    test_linode_client: LinodeClient,
    bucket: ObjectStorageBucket,
):
    loaded_bucket = test_linode_client.load(ObjectStorageBucket, bucket.label)

    assert loaded_bucket.label == bucket.label
    assert loaded_bucket.region == bucket.region


def test_bucket(
    test_linode_client: LinodeClient,
    bucket: ObjectStorageBucket,
    region: str,
):
    buckets = test_linode_client.object_storage.buckets_in_region(region=region)
    assert len(buckets) >= 1
    assert any(b.label == bucket.label for b in buckets)

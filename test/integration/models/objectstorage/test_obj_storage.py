import time
from test.integration.conftest import get_region

import pytest

from linode_api4.objects import (
    ObjectStorageACL,
    ObjectStorageBucket,
    ObjectStorageCluster,
    ObjectStorageKeys,
)


@pytest.fixture(scope="session")
def test_object_storage_bucket(test_linode_client):
    client = test_linode_client

    region = get_region(client, {"Object Storage"})
    cluster_region_name = region.id + "-1"
    label = str(time.time_ns())[:-5] + "-bucket"

    bucket = client.object_storage.bucket_create(
        cluster=cluster_region_name, label=label
    )

    yield bucket

    bucket.delete()


def test_list_obj_storage_bucket(
    test_linode_client, test_object_storage_bucket
):
    client = test_linode_client

    buckets = client.object_storage.buckets()
    target_bucket = test_object_storage_bucket

    bucket_ids = [bucket.id for bucket in buckets]

    assert target_bucket.id in bucket_ids
    assert isinstance(target_bucket, ObjectStorageBucket)


def test_bucket_access_modify(test_object_storage_bucket):
    bucket = test_object_storage_bucket

    res = bucket.access_modify(ObjectStorageACL.PRIVATE, cors_enabled=True)

    assert res


def test_bucket_access_update(test_object_storage_bucket):
    bucket = test_object_storage_bucket
    res = bucket.access_update(ObjectStorageACL.PRIVATE, cors_enabled=True)

    assert res


def test_get_ssl_cert(test_object_storage_bucket):
    bucket = test_object_storage_bucket

    res = bucket.ssl_cert().ssl

    assert res is False


def test_create_key_for_specific_bucket(
    test_linode_client, test_object_storage_bucket
):
    client = test_linode_client
    bucket = test_object_storage_bucket
    keys = client.object_storage.keys_create(
        "restricted-keys",
        bucket_access=client.object_storage.bucket_access(
            bucket.cluster, bucket.id, "read_write"
        ),
    )

    assert isinstance(keys, ObjectStorageKeys)
    assert keys.bucket_access[0].bucket_name == bucket.id
    assert keys.bucket_access[0].permissions == "read_write"
    assert keys.bucket_access[0].cluster == bucket.cluster


def test_get_cluster(test_linode_client, test_object_storage_bucket):
    client = test_linode_client
    bucket = test_object_storage_bucket

    cluster = client.load(ObjectStorageCluster, bucket.cluster)

    assert "linodeobjects.com" in cluster.domain
    assert cluster.id == bucket.cluster
    assert "available" == cluster.status


def test_get_buckets_in_cluster(test_linode_client, test_object_storage_bucket):
    client = test_linode_client
    bucket = test_object_storage_bucket

    cluster = client.load(ObjectStorageCluster, bucket.cluster)
    buckets = cluster.buckets_in_cluster()
    bucket_ids = [bucket.id for bucket in buckets]

    assert bucket.id in bucket_ids

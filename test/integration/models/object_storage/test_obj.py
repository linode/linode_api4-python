import time
from test.integration.helpers import send_request_when_resource_available

import pytest

from linode_api4.common import RegionPrice
from linode_api4.linode_client import LinodeClient
from linode_api4.objects.object_storage import (
    ObjectStorageACL,
    ObjectStorageBucket,
    ObjectStorageCluster,
    ObjectStorageEndpointType,
    ObjectStorageKeyPermission,
    ObjectStorageKeys,
    ObjectStorageType,
)


@pytest.fixture(scope="session")
def region(test_linode_client: LinodeClient):
    return "us-southeast"  # uncomment get_region(test_linode_client, {"Object Storage"}).id


@pytest.fixture(scope="session")
def endpoints(test_linode_client: LinodeClient):
    return test_linode_client.object_storage.endpoints()


@pytest.fixture(scope="session")
def bucket(
    test_linode_client: LinodeClient, region: str
) -> ObjectStorageBucket:
    bucket = test_linode_client.object_storage.bucket_create(
        cluster_or_region=region,
        label="bucket-" + str(time.time_ns()),
        acl=ObjectStorageACL.PRIVATE,
        cors_enabled=False,
    )

    yield bucket
    send_request_when_resource_available(timeout=100, func=bucket.delete)


@pytest.fixture(scope="session")
def bucket_with_endpoint(
    test_linode_client: LinodeClient, endpoints
) -> ObjectStorageBucket:
    selected_endpoint = next(
        (
            e
            for e in endpoints
            if e.endpoint_type == ObjectStorageEndpointType.E1
        ),
        None,
    )

    bucket = test_linode_client.object_storage.bucket_create(
        cluster_or_region=selected_endpoint.region,
        label="bucket-" + str(time.time_ns()),
        acl=ObjectStorageACL.PRIVATE,
        cors_enabled=False,
        endpoint_type=selected_endpoint.endpoint_type,
    )

    yield bucket

    send_request_when_resource_available(timeout=100, func=bucket.delete)


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
    assert (
        loaded_limited_key.regions[0].endpoint_type
        in ObjectStorageEndpointType.__members__.values()
    )


def test_bucket(test_linode_client: LinodeClient, bucket: ObjectStorageBucket):
    loaded_bucket = test_linode_client.load(
        ObjectStorageBucket,
        target_id=bucket.label,
        target_parent_id=bucket.region,
    )

    assert loaded_bucket.label == bucket.label
    assert loaded_bucket.region == bucket.region


def test_bucket_with_endpoint(
    test_linode_client: LinodeClient, bucket_with_endpoint: ObjectStorageBucket
):
    loaded_bucket = test_linode_client.load(
        ObjectStorageBucket,
        target_id=bucket_with_endpoint.label,
        target_parent_id=bucket_with_endpoint.region,
    )

    assert loaded_bucket.label == bucket_with_endpoint.label
    assert loaded_bucket.region == bucket_with_endpoint.region
    assert loaded_bucket.s3_endpoint is not None
    assert loaded_bucket.endpoint_type == "E1"


def test_buckets_in_region(
    test_linode_client: LinodeClient,
    bucket: ObjectStorageBucket,
    region: str,
):
    buckets = test_linode_client.object_storage.buckets_in_region(region=region)
    assert len(buckets) >= 1
    assert any(b.label == bucket.label for b in buckets)


@pytest.mark.smoke
def test_list_obj_storage_bucket(
    test_linode_client: LinodeClient,
    bucket: ObjectStorageBucket,
):
    buckets = test_linode_client.object_storage.buckets()
    target_bucket_id = bucket.id
    assert any(target_bucket_id == b.id for b in buckets)


def test_bucket_access_get(bucket: ObjectStorageBucket):
    access = bucket.access_get()

    assert access.acl is not None
    assert access.acl_xml is not None
    assert access.cors_enabled is not None


def test_bucket_access_modify(bucket: ObjectStorageBucket):
    bucket.access_modify(ObjectStorageACL.PRIVATE, cors_enabled=True)


def test_bucket_access_update(bucket: ObjectStorageBucket):
    bucket.access_update(ObjectStorageACL.PRIVATE, cors_enabled=True)


def test_get_ssl_cert(bucket: ObjectStorageBucket):
    assert not bucket.ssl_cert().ssl


def test_get_cluster(
    test_linode_client: LinodeClient, bucket: ObjectStorageBucket
):
    cluster = test_linode_client.load(ObjectStorageCluster, bucket.cluster)

    assert "linodeobjects.com" in cluster.domain
    assert cluster.id == bucket.cluster
    assert "available" == cluster.status


def test_get_buckets_in_cluster(
    test_linode_client: LinodeClient, bucket: ObjectStorageBucket
):
    cluster = test_linode_client.load(ObjectStorageCluster, bucket.cluster)
    assert any(bucket.id == b.id for b in cluster.buckets_in_cluster())


def test_object_storage_types(test_linode_client):
    types = test_linode_client.object_storage.types()

    if len(types) > 0:
        for object_storage_type in types:
            assert type(object_storage_type) is ObjectStorageType
            assert object_storage_type.price.monthly is None or (
                isinstance(object_storage_type.price.monthly, (float, int))
                and object_storage_type.price.monthly >= 0
            )
            if len(object_storage_type.region_prices) > 0:
                region_price = object_storage_type.region_prices[0]
                assert type(region_price) is RegionPrice
                assert object_storage_type.price.monthly is None or (
                    isinstance(object_storage_type.price.monthly, (float, int))
                    and object_storage_type.price.monthly >= 0
                )

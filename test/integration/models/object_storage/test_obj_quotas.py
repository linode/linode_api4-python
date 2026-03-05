import pytest

from linode_api4.errors import ApiError
from linode_api4.objects.object_storage import (
    ObjectStorageGlobalQuota,
    ObjectStorageQuota,
    ObjectStorageQuotaUsage,
)


def test_list_and_get_obj_storage_quotas(test_linode_client):
    quotas = test_linode_client.object_storage.quotas()

    if len(quotas) < 1:
        pytest.skip("No available quota for testing. Skipping now...")

    found_quota = quotas[0]

    get_quota = test_linode_client.load(
        ObjectStorageQuota, found_quota.quota_id
    )

    assert found_quota.quota_id == get_quota.quota_id
    assert found_quota.quota_name == get_quota.quota_name
    assert found_quota.endpoint_type == get_quota.endpoint_type
    assert found_quota.s3_endpoint == get_quota.s3_endpoint
    assert found_quota.description == get_quota.description
    assert found_quota.quota_limit == get_quota.quota_limit
    assert found_quota.resource_metric == get_quota.resource_metric
    assert found_quota.quota_type == get_quota.quota_type
    assert found_quota.has_usage == get_quota.has_usage


def test_get_obj_storage_quota_usage(test_linode_client):
    quotas = test_linode_client.object_storage.quotas()

    if len(quotas) < 1:
        pytest.skip("No available quota for testing. Skipping now...")

    quota_with_usage = next((quota for quota in quotas if quota.has_usage), None)

    if quota_with_usage is None:
        quota_id = quotas[0].quota_id
        quota = test_linode_client.load(ObjectStorageQuota, quota_id)

        with pytest.raises(ApiError) as exc:
            quota.usage()

        assert exc.value.status == 404
        assert "Usage not supported" in str(exc.value)
        return

    quota_id = quota_with_usage.quota_id
    quota = test_linode_client.load(ObjectStorageQuota, quota_id)

    quota_usage = quota.usage()

    assert isinstance(quota_usage, ObjectStorageQuotaUsage)
    assert quota_usage.quota_limit >= 0

    if quota_usage.usage is not None:
        assert quota_usage.usage >= 0


def test_list_and_get_obj_storage_global_quotas(test_linode_client):
    try:
        quotas = test_linode_client.object_storage.global_quotas()
    except ApiError as err:
        if err.status == 404:
            pytest.skip("Object Storage is not enabled on this account.")
        raise

    if len(quotas) < 1:
        pytest.skip("No available global quota for testing. Skipping now...")

    found_quota = quotas[0]

    get_quota = test_linode_client.load(
        ObjectStorageGlobalQuota, found_quota.quota_id
    )

    assert found_quota.quota_id == get_quota.quota_id
    assert found_quota.quota_type == get_quota.quota_type
    assert found_quota.quota_name == get_quota.quota_name
    assert found_quota.description == get_quota.description
    assert found_quota.resource_metric == get_quota.resource_metric
    assert found_quota.quota_limit == get_quota.quota_limit
    assert found_quota.has_usage == get_quota.has_usage


def test_get_obj_storage_global_quota_usage(test_linode_client):
    try:
        quotas = test_linode_client.object_storage.global_quotas()
    except ApiError as err:
        if err.status == 404:
            pytest.skip("Object Storage is not enabled on this account.")
        raise

    if len(quotas) < 1:
        pytest.skip("No available global quota for testing. Skipping now...")

    quota_with_usage = next((quota for quota in quotas if quota.has_usage), None)

    if quota_with_usage is None:
        quota_id = quotas[0].quota_id
        quota = test_linode_client.load(ObjectStorageGlobalQuota, quota_id)

        with pytest.raises(ApiError) as exc:
            quota.usage()

        assert exc.value.status == 404
        assert "Usage not supported" in str(exc.value)
        return

    quota_id = quota_with_usage.quota_id
    quota = test_linode_client.load(ObjectStorageGlobalQuota, quota_id)

    quota_usage = quota.usage()

    assert isinstance(quota_usage, ObjectStorageQuotaUsage)
    assert quota_usage.quota_limit >= 0

    if quota_usage.usage is not None:
        assert quota_usage.usage >= 0

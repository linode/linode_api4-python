import pytest

from linode_api4.objects.object_storage import (
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


def test_get_obj_storage_quota_usage(test_linode_client):
    quotas = test_linode_client.object_storage.quotas()

    if len(quotas) < 1:
        pytest.skip("No available quota for testing. Skipping now...")

    quota_id = quotas[0].quota_id
    quota = test_linode_client.load(ObjectStorageQuota, quota_id)

    quota_usage = quota.usage()

    assert isinstance(quota_usage, ObjectStorageQuotaUsage)
    assert quota_usage.quota_limit >= 0

    if quota_usage.usage is not None:
        assert quota_usage.usage >= 0

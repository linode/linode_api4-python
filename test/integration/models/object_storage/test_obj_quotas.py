from linode_api4.objects.object_storage import (
    ObjectStorageQuota,
    ObjectStorageQuotaUsage,
)


def test_list_obj_storage_quotas(test_linode_client):
    quotas = test_linode_client.object_storage.quotas()

    target_quota_id = "obj-buckets-us-sea-1.linodeobjects.com"

    found_quota = None
    for quota in quotas:
        if quota.quota_id == target_quota_id:
            found_quota = quota
            break

    assert (
        found_quota is not None
    ), f"Quota with ID {target_quota_id} not found."

    assert found_quota.quota_id == "obj-buckets-us-sea-1.linodeobjects.com"
    assert found_quota.quota_name == "max_buckets"
    assert found_quota.endpoint_type == "E1"
    assert found_quota.s3_endpoint == "us-sea-1.linodeobjects.com"
    assert (
        found_quota.description
        == "Maximum number of buckets this customer is allowed to have on this endpoint"
    )
    assert found_quota.quota_limit == 1000
    assert found_quota.resource_metric == "bucket"


def test_get_obj_storage_quota(test_linode_client):
    quota_id = "obj-objects-us-ord-1.linodeobjects.com"
    quota = test_linode_client.load(ObjectStorageQuota, quota_id)

    assert quota.quota_id == "obj-objects-us-ord-1.linodeobjects.com"
    assert quota.quota_name == "max_objects"
    assert quota.endpoint_type == "E1"
    assert quota.s3_endpoint == "us-ord-1.linodeobjects.com"
    assert (
        quota.description
        == "Maximum number of objects this customer is allowed to have on this endpoint"
    )
    assert quota.quota_limit == 100000000
    assert quota.resource_metric == "object"


def test_get_obj_storage_quota_usage(test_linode_client):
    quota_id = "obj-objects-us-ord-1.linodeobjects.com"
    quota = test_linode_client.load(ObjectStorageQuota, quota_id)

    quota_usage = quota.usage()

    assert isinstance(quota_usage, ObjectStorageQuotaUsage)
    assert quota_usage.quota_limit == 100000000
    assert quota_usage.usage >= 0

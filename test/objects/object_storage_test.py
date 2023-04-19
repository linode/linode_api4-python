from datetime import datetime
from test.base import ClientBaseCase

from linode_api4.objects import ObjectStorageBucket, BucketACL


class ObjectStorageTest(ClientBaseCase):
    """
    Test the methods of the ObjectStorage
    """

    def test_object_storage_bucket_api_get(self):
        object_storage_bucket_api_get_url = (
            "/object-storage/buckets/us-east-1/example-bucket"
        )
        with self.mock_get(object_storage_bucket_api_get_url) as m:
            object_storage_bucket = ObjectStorageBucket(
                self.client, "example-bucket", "us-east-1"
            )
            self.assertEqual(object_storage_bucket.cluster, "us-east-1")
            self.assertEqual(object_storage_bucket.label, "example-bucket")
            self.assertEqual(
                object_storage_bucket.created,
                datetime(
                    year=2019, month=1, day=1, hour=1, minute=23, second=45
                ),
            )
            self.assertEqual(
                object_storage_bucket.hostname,
                "example-bucket.us-east-1.linodeobjects.com",
            )
            self.assertEqual(object_storage_bucket.objects, 4)
            self.assertEqual(object_storage_bucket.size, 188318981)
            self.assertEqual(m.call_url, object_storage_bucket_api_get_url)

    def test_object_storage_bucket_delete(self):
        object_storage_bucket_delete_url = (
            "/object-storage/buckets/us-east-1/example-bucket"
        )
        with self.mock_delete() as m:
            object_storage_bucket = ObjectStorageBucket(
                self.client, "example-bucket", "us-east-1"
            )
            object_storage_bucket.delete()
            self.assertEqual(m.call_url, object_storage_bucket_delete_url)

    def test_bucket_access_modify(self):
        """
        Test that you can modify bucket access settings.
        """
        bucket_access_modify_url = (
            "/object-storage/buckets/us-east-1/example-bucket/access"
        )
        with self.mock_post({}) as m:
            object_storage_bucket = ObjectStorageBucket(
                self.client, "example-bucket", "us-east-1"
            )
            object_storage_bucket.access_modify(
                "us-east-1", "example-bucket", BucketACL.PRIVATE, True
            )
            self.assertEqual(
                m.call_data,
                {
                    "acl": "private",
                    "cors_enabled": True,
                },
            )
            self.assertEqual(m.call_url, bucket_access_modify_url)

    def test_bucket_access_update(self):
        """
        Test that you can update bucket access settings.
        """
        bucket_access_update_url = (
            "/object-storage/buckets/us-east-1/example-bucket/access"
        )
        with self.mock_put({}) as m:
            object_storage_bucket = ObjectStorageBucket(
                self.client, "example-bucket", "us-east-1"
            )
            object_storage_bucket.access_update(
                "us-east-1", "example-bucket", BucketACL.PRIVATE, True
            )
            self.assertEqual(
                m.call_data,
                {
                    "acl": "private",
                    "cors_enabled": True,
                },
            )
            self.assertEqual(m.call_url, bucket_access_update_url)

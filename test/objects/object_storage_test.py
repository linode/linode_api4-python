from test.base import ClientBaseCase
from linode_api4.objects import ObjectStorageBucket

class ObjectStorageTest(ClientBaseCase):
    """
    Test the methods of the ObjectStorage
    """
    def test_object_storage_bucket_api_get(self):
        object_storage_bucket_api_get_url = "/object-storage/buckets/us-east-1/example-bucket"        
        with self.mock_get(object_storage_bucket_api_get_url) as m:
            object_storage_bucket = ObjectStorageBucket(self.client, "example-bucket", "us-east-1")
            object_storage_bucket._api_get()
            self.assertEqual(object_storage_bucket.cluster, "us-east-1")
            self.assertEqual(m.call_url, object_storage_bucket_api_get_url)

    def test_object_storage_bucket_delete(self):
        object_storage_bucket_delete_url = "/object-storage/buckets/us-east-1/example-bucket"
        with self.mock_delete() as m:
            object_storage_bucket = ObjectStorageBucket(self.client, "example-bucket", "us-east-1")
            object_storage_bucket.delete()
            self.assertEqual(m.call_url, object_storage_bucket_delete_url)



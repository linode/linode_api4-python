from datetime import datetime
from test.unit.base import ClientBaseCase

from linode_api4.objects import (
    ObjectStorageACL,
    ObjectStorageBucket,
    ObjectStorageCluster,
)


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
            object_storage_bucket.access_modify(ObjectStorageACL.PRIVATE, True)
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
            object_storage_bucket.access_update(ObjectStorageACL.PRIVATE, True)
            self.assertEqual(
                m.call_data,
                {
                    "acl": "private",
                    "cors_enabled": True,
                },
            )
            self.assertEqual(m.call_url, bucket_access_update_url)

    def test_buckets_in_cluster(self):
        """
        Test that Object Storage Buckets in a specified cluster can be reterived
        """
        buckets_in_cluster_url = "/object-storage/buckets/us-east-1"
        with self.mock_get(buckets_in_cluster_url) as m:
            cluster = ObjectStorageCluster(self.client, "us-east-1")
            buckets = cluster.buckets_in_cluster()
            self.assertIsNotNone(buckets)
            bucket = buckets[0]

            self.assertEqual(m.call_url, buckets_in_cluster_url)
            self.assertEqual(bucket.cluster, "us-east-1")
            self.assertEqual(
                bucket.created,
                datetime(
                    year=2019, month=1, day=1, hour=1, minute=23, second=45
                ),
            )
            self.assertEqual(
                bucket.hostname, "example-bucket.us-east-1.linodeobjects.com"
            )
            self.assertEqual(bucket.label, "example-bucket")
            self.assertEqual(bucket.objects, 4)
            self.assertEqual(bucket.size, 188318981)

    def test_ssl_cert_delete(self):
        """
        Test that you can delete the TLS/SSL certificate and private key of a bucket.
        """
        ssl_cert_delete_url = (
            "/object-storage/buckets/us-east-1/example-bucket/ssl"
        )
        with self.mock_delete() as m:
            object_storage_bucket = ObjectStorageBucket(
                self.client, "example-bucket", "us-east-1"
            )
            object_storage_bucket.ssl_cert_delete()
            self.assertEqual(m.call_url, ssl_cert_delete_url)

    def test_ssl_cert(self):
        """
        Test tha you can get a bool value indicating if this bucket
        has a corresponding TLS/SSL certificate.
        """
        ssl_cert_url = "/object-storage/buckets/us-east-1/example-bucket/ssl"
        with self.mock_get(ssl_cert_url) as m:
            object_storage_bucket = ObjectStorageBucket(
                self.client, "example-bucket", "us-east-1"
            )
            result = object_storage_bucket.ssl_cert()
            self.assertIsNotNone(result)
            self.assertEqual(m.call_url, ssl_cert_url)
            self.assertEqual(result.ssl, True)

    def test_ssl_cert_upload(self):
        """
        Test that you can upload a TLS/SSL cert.
        """
        ssl_cert_upload_url = (
            "/object-storage/buckets/us-east-1/example-bucket/ssl"
        )
        with self.mock_post(ssl_cert_upload_url) as m:
            object_storage_bucket = ObjectStorageBucket(
                self.client, "example-bucket", "us-east-1"
            )
            result = object_storage_bucket.ssl_cert_upload(
                "-----BEGIN CERTIFICATE-----\nCERTIFICATE_INFORMATION\n-----END CERTIFICATE-----",
                "-----BEGIN PRIVATE KEY-----\nPRIVATE_KEY_INFORMATION\n-----END PRIVATE KEY-----",
            )
            self.assertIsNotNone(result)
            self.assertEqual(m.call_url, ssl_cert_upload_url)
            self.assertEqual(result.ssl, True)
            self.assertEqual(
                m.call_data,
                {
                    "certificate": "-----BEGIN CERTIFICATE-----\nCERTIFICATE_INFORMATION\n-----END CERTIFICATE-----",
                    "private_key": "-----BEGIN PRIVATE KEY-----\nPRIVATE_KEY_INFORMATION\n-----END PRIVATE KEY-----",
                },
            )

    def test_contents(self):
        """
        Test that you can get the contents of a bucket.
        """
        bucket_contents_url = (
            "/object-storage/buckets/us-east-1/example-bucket/object-list"
        )
        with self.mock_get(bucket_contents_url) as m:
            object_storage_bucket = ObjectStorageBucket(
                self.client, "example-bucket", "us-east-1"
            )
            contents = object_storage_bucket.contents()
            self.assertIsNotNone(contents)
            content = contents[0]

            self.assertEqual(m.call_url, bucket_contents_url)
            self.assertEqual(content.etag, "9f254c71e28e033bf9e0e5262e3e72ab")
            self.assertEqual(content.is_truncated, True)
            self.assertEqual(content.last_modified, "2019-01-01T01:23:45")
            self.assertEqual(content.name, "example")
            self.assertEqual(
                content.next_marker,
                "bd021c21-e734-4823-97a4-58b41c2cd4c8.892602.184",
            )
            self.assertEqual(
                content.owner, "bfc70ab2-e3d4-42a4-ad55-83921822270c"
            )
            self.assertEqual(content.size, 123)
            self.assertEqual(
                m.call_data,
                {
                    "page_size": 100,
                },
            )

    def test_object_acl_config(self):
        """
        Test that you can view an Object’s configured Access Control List (ACL) in this Object Storage bucket.
        """
        object_acl_config_url = (
            "/object-storage/buckets/us-east-1/example-bucket/object-acl"
        )
        with self.mock_get(object_acl_config_url) as m:
            object_storage_bucket = ObjectStorageBucket(
                self.client, "example-bucket", "us-east-1"
            )
            acl = object_storage_bucket.object_acl_config("example")
            self.assertEqual(m.call_url, object_acl_config_url)
            self.assertEqual(acl.acl, "public-read")
            self.assertEqual(
                acl.acl_xml, "<AccessControlPolicy>...</AccessControlPolicy>"
            )
            self.assertEqual(
                m.call_data,
                {
                    "name": "example",
                },
            )

    def test_object_acl_config_update(self):
        """
        Test that you can update an Object’s configured Access Control List (ACL) in this Object Storage bucket.
        """
        object_acl_config_update_url = (
            "/object-storage/buckets/us-east-1/example-bucket/object-acl"
        )
        with self.mock_put(object_acl_config_update_url) as m:
            object_storage_bucket = ObjectStorageBucket(
                self.client, "example-bucket", "us-east-1"
            )
            acl = object_storage_bucket.object_acl_config_update(
                ObjectStorageACL.PUBLIC_READ,
                "example",
            )
            self.assertEqual(m.call_url, object_acl_config_update_url)
            self.assertEqual(acl.acl, "public-read")
            self.assertEqual(
                acl.acl_xml, "<AccessControlPolicy>...</AccessControlPolicy>"
            )
            self.assertEqual(
                m.call_data,
                {
                    "acl": "public-read",
                    "name": "example",
                },
            )

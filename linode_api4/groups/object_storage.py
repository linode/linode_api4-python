from urllib import parse

from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import (
    Base,
    MappedObject,
    ObjectStorageACL,
    ObjectStorageBucket,
    ObjectStorageCluster,
    ObjectStorageKeys,
)
from linode_api4.util import drop_null_keys


class ObjectStorageGroup(Group):
    """
    This group encapsulates all endpoints under /object-storage, including viewing
    available clusters, buckets, and managing keys and TLS/SSL certs, etc.
    """

    def clusters(self, *filters):
        """
        Returns a list of available Object Storage Clusters.  You may filter
        this query to return only Clusters that are available in a specific region::

           us_east_clusters = client.object_storage.clusters(ObjectStorageCluster.region == "us-east")

        API Documentation: https://www.linode.com/docs/api/object-storage/#clusters-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Object Storage Clusters that matched the query.
        :rtype: PaginatedList of ObjectStorageCluster
        """
        return self.client._get_and_filter(ObjectStorageCluster, *filters)

    def keys(self, *filters):
        """
        Returns a list of Object Storage Keys active on this account.  These keys
        allow third-party applications to interact directly with Linode Object Storage.

        API Documentation: https://www.linode.com/docs/api/object-storage/#object-storage-keys-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Object Storage Keys that matched the query.
        :rtype: PaginatedList of ObjectStorageKeys
        """
        return self.client._get_and_filter(ObjectStorageKeys, *filters)

    def keys_create(self, label, bucket_access=None):
        """
        Creates a new Object Storage keypair that may be used to interact directly
        with Linode Object Storage in third-party applications.  This response is
        the only time that "secret_key" will be populated - be sure to capture its
        value or it will be lost forever.

        If given, `bucket_access` will cause the new keys to be restricted to only
        the specified level of access for the specified buckets.  For example, to
        create a keypair that can only access the "example" bucket in all clusters
        (and assuming you own that bucket in every cluster), you might do this::

           client = LinodeClient(TOKEN)

           # look up clusters
           all_clusters = client.object_storage.clusters()

           new_keys = client.object_storage.keys_create(
               "restricted-keys",
               bucket_access=[
                   client.object_storage.bucket_access(cluster, "example", "read_write")
                   for cluster in all_clusters
               ],
           )

        To create a keypair that can only read from the bucket "example2" in the
        "us-east-1" cluster (an assuming you own that bucket in that cluster),
        you might do this::

           client = LinodeClient(TOKEN)
           new_keys_2 = client.object_storage.keys_create(
               "restricted-keys-2",
               bucket_access=client.object_storage.bucket_access("us-east-1", "example2", "read_only"),
           )

        API Documentation: https://www.linode.com/docs/api/object-storage/#object-storage-key-create

        :param label: The label for this keypair, for identification only.
        :type label: str
        :param bucket_access: One or a list of dicts with keys "cluster,"
                              "permissions", and "bucket_name".  If given, the
                              resulting Object Storage keys will only have the
                              requested level of access to the requested buckets,
                              if they exist and are owned by you.  See the provided
                              :any:`bucket_access` function for a convenient way
                              to create these dicts.
        :type bucket_access: dict or list of dict

        :returns: The new keypair, with the secret key populated.
        :rtype: ObjectStorageKeys
        """
        params = {"label": label}

        if bucket_access is not None:
            if not isinstance(bucket_access, list):
                bucket_access = [bucket_access]

            ba = [
                {
                    "permissions": c.get("permissions"),
                    "bucket_name": c.get("bucket_name"),
                    "cluster": c.id
                    if "cluster" in c and issubclass(type(c["cluster"]), Base)
                    else c.get("cluster"),
                }
                for c in bucket_access
            ]

            params["bucket_access"] = ba

        result = self.client.post("/object-storage/keys", data=params)

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating Object Storage Keys!",
                json=result,
            )

        ret = ObjectStorageKeys(self.client, result["id"], result)
        return ret

    def bucket_access(self, cluster, bucket_name, permissions):
        return ObjectStorageBucket.access(
            self, cluster, bucket_name, permissions
        )

    def cancel(self):
        """
        Cancels Object Storage service.  This may be a destructive operation.  Once
        cancelled, you will no longer receive the transfer for or be billed for
        Object Storage, and all keys will be invalidated.

        API Documentation: https://www.linode.com/docs/api/object-storage/#object-storage-cancel
        """
        self.client.post("/object-storage/cancel", data={})
        return True

    def transfer(self):
        """
        The amount of outbound data transfer used by your account’s Object Storage buckets,
        in bytes, for the current month’s billing cycle. Object Storage adds 1 terabyte
        of outbound data transfer to your data transfer pool.

        API Documentation: https://www.linode.com/docs/api/object-storage/#object-storage-transfer-view

        :returns: The amount of outbound data transfer used by your account’s Object
                  Storage buckets, in bytes, for the current month’s billing cycle.
        :rtype: MappedObject
        """
        result = self.client.get("/object-storage/transfer")

        if not "used" in result:
            raise UnexpectedResponseError(
                "Unexpected response when getting Transfer Pool!",
                json=result,
            )

        return MappedObject(**result)

    def buckets(self, *filters):
        """
        Returns a paginated list of all Object Storage Buckets that you own.
        This endpoint is available for convenience.
        It is recommended that instead you use the more fully-featured S3 API directly.

        API Documentation: https://www.linode.com/docs/api/object-storage/#object-storage-buckets-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Object Storage Buckets that matched the query.
        :rtype: PaginatedList of ObjectStorageBucket
        """
        return self.client._get_and_filter(ObjectStorageBucket, *filters)

    def bucket_create(
        self,
        cluster,
        label,
        acl: ObjectStorageACL = ObjectStorageACL.PRIVATE,
        cors_enabled=False,
    ):
        """
        Creates an Object Storage Bucket in the specified cluster. Accounts with
        negative balances cannot access this command. If the bucket already exists
        and is owned by you, this endpoint returns a 200 response with that bucket
        as if it had just been created.

        This endpoint is available for convenience.
        It is recommended that instead you use the more fully-featured S3 API directly.

        API Documentation: https://www.linode.com/docs/api/object-storage/#object-storage-bucket-create

        :param acl: The Access Control Level of the bucket using a canned ACL string.
                    For more fine-grained control of ACLs, use the S3 API directly.
        :type acl: str
                   Enum: private,public-read,authenticated-read,public-read-write

        :param cluster: The ID of the Object Storage Cluster where this bucket
                        should be created.
        :type cluster: str

        :param cors_enabled: If true, the bucket will be created with CORS enabled for
                             all origins. For more fine-grained controls of CORS, use
                             the S3 API directly.
        :type cors_enabled: bool

        :param label: The name for this bucket. Must be unique in the cluster you are
                      creating the bucket in, or an error will be returned. Labels will
                      be reserved only for the cluster that active buckets are created
                      and stored in. If you want to reserve this bucket’s label in
                      another cluster, you must create a new bucket with the same label
                      in the new cluster.
        :type label: str

        :returns: A Object Storage Buckets that created by user.
        :rtype: ObjectStorageBucket
        """
        cluster_id = (
            cluster.id if isinstance(cluster, ObjectStorageCluster) else cluster
        )

        params = {
            "cluster": cluster_id,
            "label": label,
            "acl": acl,
            "cors_enabled": cors_enabled,
        }

        result = self.client.post("/object-storage/buckets", data=params)

        if not "label" in result or not "cluster" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating Object Storage Bucket!",
                json=result,
            )

        return ObjectStorageBucket(
            self.client, result["label"], result["cluster"], result
        )

    def object_acl_config(self, cluster_id, bucket, name=None):
        return ObjectStorageBucket(
            self.client, bucket, cluster_id
        ).object_acl_config(name)

    def object_acl_config_update(
        self, cluster_id, bucket, acl: ObjectStorageACL, name
    ):
        return ObjectStorageBucket(
            self.client, bucket, cluster_id
        ).object_acl_config_update(acl, name)

    def object_url_create(
        self,
        cluster_id,
        bucket,
        method,
        name,
        content_type=None,
        expires_in=3600,
    ):
        """
        Creates a pre-signed URL to access a single Object in a bucket.
        This can be used to share objects, and also to create/delete objects by using
        the appropriate HTTP method in your request body’s method parameter.

        This endpoint is available for convenience.
        It is recommended that instead you use the more fully-featured S3 API directly.

        API Documentation: https://www.linode.com/docs/api/object-storage/#object-storage-object-url-create

        :param cluster_id: The ID of the cluster this bucket exists in.
        :type cluster_id: str

        :param bucket: The bucket name.
        :type bucket: str

        :param content_type: The expected Content-type header of the request this
                             signed URL will be valid for. If provided, the
                             Content-type header must be sent with the request when
                             this URL is used, and must be the same as it was when
                             the signed URL was created.
                             Required for all methods except “GET” or “DELETE”.
        :type content_type: str

        :param expires_in: How long this signed URL will be valid for, in seconds.
                           If omitted, the URL will be valid for 3600 seconds (1 hour). Defaults to 3600.
        :type expires_in: int 360..86400

        :param method: The HTTP method allowed to be used with the pre-signed URL.
        :type method: str

        :param name: The name of the object that will be accessed with the pre-signed
                     URL. This object need not exist, and no error will be returned
                     if it doesn’t. This behavior is useful for generating pre-signed
                     URLs to upload new objects to by setting the method to “PUT”.
        :type name: str

        :returns: The signed URL to perform the request at.
        :rtype: MappedObject
        """
        if method not in ("GET", "DELETE") and content_type is None:
            raise ValueError(
                "Content-type header is missing for the current method! It's required for all methods except GET or DELETE."
            )
        params = {
            "method": method,
            "name": name,
            "expires_in": expires_in,
            "content_type": content_type,
        }

        result = self.client.post(
            "/object-storage/buckets/{}/{}/object-url".format(
                parse.quote(str(cluster_id)), parse.quote(str(bucket))
            ),
            data=drop_null_keys(params),
        )

        if not "url" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating the access url of an object!",
                json=result,
            )

        return MappedObject(**result)

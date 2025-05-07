import re
import warnings
from typing import List, Optional, Union
from urllib import parse

from deprecated import deprecated

from linode_api4 import (
    ObjectStorageEndpoint,
    ObjectStorageEndpointType,
    ObjectStorageType,
    PaginatedList,
)
from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import (
    Base,
    MappedObject,
    ObjectStorageACL,
    ObjectStorageBucket,
    ObjectStorageCluster,
    ObjectStorageKeyPermission,
    ObjectStorageKeys,
    ObjectStorageQuota,
)
from linode_api4.util import drop_null_keys


class ObjectStorageGroup(Group):
    """
    This group encapsulates all endpoints under /object-storage, including viewing
    available clusters, buckets, and managing keys and TLS/SSL certs, etc.
    """

    @deprecated(
        reason="deprecated to use regions list API for listing available OJB clusters"
    )
    def clusters(self, *filters):
        """
        This endpoint will be deprecated to use the regions list API to list available OBJ clusters,
        and a new access key API will directly expose the S3 endpoint hostname.

        Returns a list of available Object Storage Clusters.  You may filter
        this query to return only Clusters that are available in a specific region::

           us_east_clusters = client.object_storage.clusters(ObjectStorageCluster.region == "us-east")

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-object-storage-clusters

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

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-object-storage-keys

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Object Storage Keys that matched the query.
        :rtype: PaginatedList of ObjectStorageKeys
        """
        return self.client._get_and_filter(ObjectStorageKeys, *filters)

    def types(self, *filters):
        """
        Returns a paginated list of Object Storage Types.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-object-storage-types

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A Paginated List of Object Storage types that match the query.
        :rtype: PaginatedList of ObjectStorageType
        """

        return self.client._get_and_filter(
            ObjectStorageType, *filters, endpoint="/object-storage/types"
        )

    def keys_create(
        self,
        label: str,
        bucket_access: Optional[Union[dict, List[dict]]] = None,
        regions: Optional[List[str]] = None,
    ):
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

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-object-storage-keys

        :param label: The label for this keypair, for identification only.
        :type label: str
        :param bucket_access: One or a list of dicts with keys "cluster," "region",
                              "permissions", and "bucket_name". "cluster" key is
                              deprecated because multiple cluster can be placed
                              in the same region. Please consider switching to
                              regions. If given, the resulting Object Storage keys
                              will only have the requested level of access to the
                              requested buckets, if they exist and are owned by
                              you.  See the provided :any:`bucket_access` function
                              for a convenient way to create these dicts.
        :type bucket_access: Optional[Union[dict, List[dict]]]

        :returns: The new keypair, with the secret key populated.
        :rtype: ObjectStorageKeys
        """
        params = {"label": label}

        if bucket_access is not None:
            if not isinstance(bucket_access, list):
                bucket_access = [bucket_access]

            ba = []
            for access_rule in bucket_access:
                access_rule_json = {
                    "permissions": access_rule.get("permissions"),
                    "bucket_name": access_rule.get("bucket_name"),
                }

                if "region" in access_rule:
                    access_rule_json["region"] = access_rule.get("region")
                elif "cluster" in access_rule:
                    warnings.warn(
                        "'cluster' is a deprecated attribute, "
                        "please consider using 'region' instead.",
                        DeprecationWarning,
                    )
                    access_rule_json["cluster"] = (
                        access_rule.id
                        if "cluster" in access_rule
                        and issubclass(type(access_rule["cluster"]), Base)
                        else access_rule.get("cluster")
                    )

                ba.append(access_rule_json)

            params["bucket_access"] = ba

        if regions is not None:
            params["regions"] = regions

        result = self.client.post("/object-storage/keys", data=params)

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating Object Storage Keys!",
                json=result,
            )

        ret = ObjectStorageKeys(self.client, result["id"], result)
        return ret

    @classmethod
    def bucket_access(
        cls,
        cluster_or_region: str,
        bucket_name: str,
        permissions: Union[str, ObjectStorageKeyPermission],
    ):
        """
        Returns a dict formatted to be included in the `bucket_access` argument
        of :any:`keys_create`.  See the docs for that method for an example of
        usage.

        :param cluster_or_region: The region or Object Storage cluster to grant access in.
        :type cluster_or_region: str
        :param bucket_name: The name of the bucket to grant access to.
        :type bucket_name: str
        :param permissions: The permissions to grant.  Should be one of "read_only"
                            or "read_write".
        :type permissions: Union[str, ObjectStorageKeyPermission]
        :param use_region: Whether to use region mode.
        :type use_region: bool

        :returns: A dict formatted correctly for specifying bucket access for
                  new keys.
        :rtype: dict
        """

        result = {
            "bucket_name": bucket_name,
            "permissions": permissions,
        }

        if cls.is_cluster(cluster_or_region):
            warnings.warn(
                "Cluster ID for Object Storage APIs has been deprecated. "
                "Please consider switch to a region ID (e.g., from `us-mia-1` to `us-mia`)",
                DeprecationWarning,
            )
            result["cluster"] = cluster_or_region
        else:
            result["region"] = cluster_or_region

        return result

    def buckets_in_region(self, region: str, *filters):
        """
        Returns a list of Buckets in the region belonging to this Account.

        This endpoint is available for convenience.
        It is recommended that instead you use the more fully-featured S3 API directly.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-object-storage-bucketin-cluster

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :param region: The ID of an object storage region (e.g. `us-mia-1`).
        :type region: str

        :returns: A list of Object Storage Buckets that in the requested cluster.
        :rtype: PaginatedList of ObjectStorageBucket
        """

        return self.client._get_and_filter(
            ObjectStorageBucket,
            *filters,
            endpoint=f"/object-storage/buckets/{region}",
        )

    def cancel(self):
        """
        Cancels Object Storage service.  This may be a destructive operation.  Once
        cancelled, you will no longer receive the transfer for or be billed for
        Object Storage, and all keys will be invalidated.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-cancel-object-storage
        """
        self.client.post("/object-storage/cancel", data={})
        return True

    def transfer(self):
        """
        The amount of outbound data transfer used by your account’s Object Storage buckets,
        in bytes, for the current month’s billing cycle. Object Storage adds 1 terabyte
        of outbound data transfer to your data transfer pool.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-object-storage-transfer

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

    def endpoints(self, *filters) -> PaginatedList:
        """
        Returns a paginated list of all Object Storage endpoints available in your account.

        This is intended to be called from the :any:`LinodeClient`
        class, like this::

           endpoints = client.object_storage.endpoints()

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-object-storage-endpoints

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Object Storage Endpoints that matched the query.
        :rtype: PaginatedList of ObjectStorageEndpoint
        """
        return self.client._get_and_filter(
            ObjectStorageEndpoint,
            *filters,
            endpoint="/object-storage/endpoints",
        )

    def buckets(self, *filters):
        """
        Returns a paginated list of all Object Storage Buckets that you own.
        This endpoint is available for convenience.
        It is recommended that instead you use the more fully-featured S3 API directly.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-object-storage-buckets

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Object Storage Buckets that matched the query.
        :rtype: PaginatedList of ObjectStorageBucket
        """
        return self.client._get_and_filter(ObjectStorageBucket, *filters)

    @staticmethod
    def is_cluster(cluster_or_region: str):
        return bool(re.match(r"^[a-z]{2}-[a-z]+-[0-9]+$", cluster_or_region))

    def bucket_create(
        self,
        cluster_or_region: Union[str, ObjectStorageCluster],
        label: str,
        acl: ObjectStorageACL = ObjectStorageACL.PRIVATE,
        cors_enabled=False,
        s3_endpoint: Optional[str] = None,
        endpoint_type: Optional[ObjectStorageEndpointType] = None,
    ):
        """
        Creates an Object Storage Bucket in the specified cluster. Accounts with
        negative balances cannot access this command. If the bucket already exists
        and is owned by you, this endpoint returns a 200 response with that bucket
        as if it had just been created.

        This endpoint is available for convenience.
        It is recommended that instead you use the more fully-featured S3 API directly.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-object-storage-bucket

        :param acl: The Access Control Level of the bucket using a canned ACL string.
                    For more fine-grained control of ACLs, use the S3 API directly.
        :type acl: str
                   Enum: private,public-read,authenticated-read,public-read-write

        :param cluster: The ID of the Object Storage Cluster where this bucket
                        should be created.
        :type cluster: str

        :param endpoint_type: The type of s3_endpoint available to the active user in this region.
        :type endpoint_type: str
                   Enum: E0,E1,E2,E3

        :param s3_endpoint: The active user's s3 endpoint URL, based on the endpoint_type and region.
        :type s3_endpoint: str

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
        cluster_or_region_id = (
            cluster_or_region.id
            if isinstance(cluster_or_region, ObjectStorageCluster)
            else cluster_or_region
        )

        params = {
            "label": label,
            "acl": acl,
            "cors_enabled": cors_enabled,
            "s3_endpoint": s3_endpoint,
            "endpoint_type": endpoint_type,
        }

        if self.is_cluster(cluster_or_region_id):
            warnings.warn(
                "The cluster parameter has been deprecated for creating a object "
                "storage bucket. Please consider switching to a region value. For "
                "example, a cluster value of `us-mia-1` can be translated to a "
                "region value of `us-mia`.",
                DeprecationWarning,
            )
            params["cluster"] = cluster_or_region_id
        else:
            params["region"] = cluster_or_region_id

        result = self.client.post("/object-storage/buckets", data=params)

        if not "label" in result or not "cluster" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating Object Storage Bucket!",
                json=result,
            )

        return ObjectStorageBucket(
            self.client, result["label"], result["cluster"], result
        )

    def object_acl_config(self, cluster_or_region_id: str, bucket, name=None):
        return ObjectStorageBucket(
            self.client, bucket, cluster_or_region_id
        ).object_acl_config(name)

    def object_acl_config_update(
        self, cluster_or_region_id, bucket, acl: ObjectStorageACL, name
    ):
        return ObjectStorageBucket(
            self.client, bucket, cluster_or_region_id
        ).object_acl_config_update(acl, name)

    def object_url_create(
        self,
        cluster_or_region_id,
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

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-object-storage-object-url

        :param cluster_or_region_id: The ID of the cluster or region this bucket exists in.
        :type cluster_or_region_id: str

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
                parse.quote(str(cluster_or_region_id)), parse.quote(str(bucket))
            ),
            data=drop_null_keys(params),
        )

        if not "url" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating the access url of an object!",
                json=result,
            )

        return MappedObject(**result)

    def quotas(self, *filters):
        """
        Lists the active ObjectStorage-related quotas applied to your account.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-object-storage-quotas

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Object Storage Quotas that matched the query.
        :rtype: PaginatedList of ObjectStorageQuota
        """
        return self.client._get_and_filter(ObjectStorageQuota, *filters)

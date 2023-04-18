from __future__ import annotations

import json
import logging
import time
from typing import BinaryIO, Tuple

import pkg_resources
import requests

from linode_api4.errors import ApiError, UnexpectedResponseError
from linode_api4.groups import *
from linode_api4.objects import *
from linode_api4.objects.filtering import Filter

from .common import SSH_KEY_TYPES, load_and_validate_keys
from .paginated_list import PaginatedList
from .util import drop_null_keys

package_version = pkg_resources.require("linode_api4")[0].version

logger = logging.getLogger(__name__)


class ObjectStorageGroup(Group):
    """
    This group encapsulates all endpoints under /object-storage, including viewing
    available clusters, buckets, and managing keys and TLS/SSL cert.
    """

    def clusters(self, *filters):
        """
        Returns a list of available Object Storage Clusters.  You may filter
        this query to return only Clusters that are available in a specific region::

           us_east_clusters = client.object_storage.clusters(ObjectStorageCluster.region == "us-east")

        API Documentation: https://www.linode.com/docs/api/object-storage/#clusters-list

        :param filters: Any number of filters to apply to this query.

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
        """
        Returns a dict formatted to be included in the `bucket_access` argument
        of :any:`keys_create`.  See the docs for that method for an example of
        usage.

        :param cluster: The Object Storage cluster to grant access in.
        :type cluster: :any:`ObjectStorageCluster` or str
        :param bucket_name: The name of the bucket to grant access to.
        :type bucket_name: str
        :param permissions: The permissions to grant.  Should be one of "read_only"
                            or "read_write".
        :type permissions: str

        :returns: A dict formatted correctly for specifying  bucket access for
                  new keys.
        :rtype: dict
        """
        return {
            "cluster": cluster,
            "bucket_name": bucket_name,
            "permissions": permissions,
        }

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
        :rtype: integer
        """
        result = self.client.get("/object-storage/transfer")

        if not "used" in result:
            raise UnexpectedResponseError(
                "Unexpected response when getting Transfer Pool!"
            )

        return MappedObject(**result)

    def buckets(self, *filters):
        """
        Returns a paginated list of all Object Storage Buckets that you own.
        This endpoint is available for convenience.
        It is recommended that instead you use the more fully-featured S3 API directly.

        API Documentation: https://www.linode.com/docs/api/object-storage/#object-storage-buckets-list

        :returns: A list of Object Storage Buckets that matched the query.
        :rtype: PaginatedList of ObjectStorageBucket
        """
        return self.client._get_and_filter(ObjectStorageBucket, *filters)

    def bucket_create(self, cluster, label, acl="private", cors_enabled=False):
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
        :type cors_enabled: boolean

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
        if acl not in (
            "private",
            "public-read",
            "authenticated-read",
            "public-read-write",
        ):
            raise ValueError("Invalid ACL value: {}".format(acl))

        params = {
            "cluster": cluster,
            "label": label,
            "acl": acl,
            "cors_enabled": cors_enabled,
        }

        result = self.client.post("/object-storage/buckets", data=params)

        if not "label" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating Object Storage Bucket!",
                json=result,
            )

        return ObjectStorageBucket(self.client, result["label"], result)

    def buckets_in_cluster(self, cluster_id, *filters):
        """
        Returns a list of Buckets in this cluster belonging to this Account.

        This endpoint is available for convenience.
        It is recommended that instead you use the more fully-featured S3 API directly.

        API Documentation: https://www.linode.com/docs/api/object-storage/#object-storage-buckets-in-cluster-list

        :param cluster_id: The ID of the cluster this bucket exists in.
        :type cluster_id: str

        :returns: A list of Object Storage Buckets that in the requested cluster.
        :rtype: PaginatedList of ObjectStorageBucket
        """

        return self.client._get_and_filter(
            ObjectStorageBucket,
            *filters,
            endpoint="/object-storage/buckets/{}".format(cluster_id),
        )

    def bucket_delete(self, cluster_id, bucket):
        """
        Delete a single bucket.

        Bucket objects must be removed prior to removing the bucket. While buckets 
        containing objects may be deleted using the s3cmd command-line tool, such 
        operations can fail if the bucket contains too many objects. The recommended 
        way to empty large buckets is to use the S3 API to configure lifecycle 
        policies that remove all objects, then delete the bucket.

        This endpoint is available for convenience.
        It is recommended that instead you use the more fully-featured S3 API directly.

        API Documentation: https://www.linode.com/docs/api/object-storage/#object-storage-bucket-remove

        :param cluster_id: The ID of the cluster this bucket exists in.
        :type cluster_id: str

        :param bucket: The bucket name.
        :type bucket: str
        """
        resp = self.client.delete(
            ObjectStorageBucket.api_endpoint.format(
                cluster=cluster_id, label=bucket
            ),
            model=self,
        )

        if "errors" in resp:
            raise UnexpectedResponseError(
                "Unexpected response when deleting a bucket!",
                json=resp,
            )
        return True

    def bucket_access_modify(
        self, cluster_id, bucket, acl=None, cors_enabled=None
    ):
        """
        Allows changing basic Cross-origin Resource Sharing (CORS) and Access Control 
        Level (ACL) settings. Only allows enabling/disabling CORS for all origins, 
        and/or setting canned ACLs. For more fine-grained control of both systems, 
        please use the more fully-featured S3 API directly.

        API Documentation: https://www.linode.com/docs/api/object-storage/#object-storage-bucket-access-modify

        :param cluster_id: The ID of the cluster this bucket exists in.
        :type cluster_id: str

        :param bucket: The bucket name.
        :type bucket: str

        :param acl: The Access Control Level of the bucket using a canned ACL string.
                    For more fine-grained control of ACLs, use the S3 API directly.
        :type acl: str
                    Enum: private,public-read,authenticated-read,public-read-write

        :param cors_enabled: If true, the bucket will be created with CORS enabled for 
                             all origins. For more fine-grained controls of CORS, use 
                             the S3 API directly.
        :type cors_enabled: boolean
        """
        params = {
            "acl": acl,
            "cors_enabled": cors_enabled,
        }

        resp = self.client.post(
            "/object-storage/buckets/{}/{}/access".format(cluster_id, bucket),
            data=drop_null_keys(params),
        )

        if "errors" in resp:
            return False
        return True

    def bucket_access_update(
        self, cluster_id, bucket, acl=None, cors_enabled=None
    ):
        """
        Allows changing basic Cross-origin Resource Sharing (CORS) and Access Control 
        Level (ACL) settings. Only allows enabling/disabling CORS for all origins, 
        and/or setting canned ACLs. For more fine-grained control of both systems, 
        please use the more fully-featured S3 API directly.

        API Documentation: https://www.linode.com/docs/api/object-storage/#object-storage-bucket-access-update

        :param cluster_id: The ID of the cluster this bucket exists in.
        :type cluster_id: str

        :param bucket: The bucket name.
        :type bucket: str

        :param acl: The Access Control Level of the bucket using a canned ACL string.
                    For more fine-grained control of ACLs, use the S3 API directly.
        :type acl: str
                    Enum: private,public-read,authenticated-read,public-read-write

        :param cors_enabled: If true, the bucket will be created with CORS enabled for 
                             all origins. For more fine-grained controls of CORS, 
                             use the S3 API directly.
        :type cors_enabled: boolean
        """
        params = {
            "acl": acl,
            "cors_enabled": cors_enabled,
        }

        resp = self.client.put(
            "/object-storage/buckets/{}/{}/access".format(cluster_id, bucket),
            data=drop_null_keys(params),
        )

        if "errors" in resp:
            return False
        return True

    def object_acl_config(self, cluster_id, bucket, name=None):
        """
        View an Object’s configured Access Control List (ACL) in this Object Storage 
        bucket. ACLs define who can access your buckets and objects and specify the 
        level of access granted to those users.

        This endpoint is available for convenience.
        It is recommended that instead you use the more fully-featured S3 API directly.

        API Documentation: https://www.linode.com/docs/api/object-storage/#object-storage-object-acl-config-view

        :param cluster_id: The ID of the cluster this bucket exists in.
        :type cluster_id: str

        :param bucket: The bucket name.
        :type bucket: str

        :param name: The name of the object for which to retrieve its Access Control 
                     List (ACL). Use the Object Storage Bucket Contents List endpoint 
                     to access all object names in a bucket.
        :type name: str

        :returns: The Object's canned ACL and policy.
        :rtype: dict {acl: str, acl_xml: str}
            :acl:
                Enum: private public-read authenticated-read public-read-write custom
                The Access Control Level of the bucket, as a canned ACL string.
                For more fine-grained control of ACLs, use the S3 API directly.
            :acl_xml:
                The full XML of the object’s ACL policy.
        """
        params = {
            "name": name,
        }
        result = self.client.get(
            "/object-storage/buckets/{}/{}/object-acl".format(
                cluster_id, bucket
            ),
            data=drop_null_keys(params),
        )

        if "errors" in result:
            raise UnexpectedResponseError(
                "Unexpected response when viewing Object’s configured ACL!",
                json=result,
            )

        return MappedObject(**result)

    def object_acl_config_update(self, cluster_id, bucket, acl, name):
        """
        Update an Object’s configured Access Control List (ACL) in this Object Storage 
        bucket. ACLs define who can access your buckets and objects and specify the 
        level of access granted to those users.

        This endpoint is available for convenience.
        It is recommended that instead you use the more fully-featured S3 API directly.

        API Documentation: https://www.linode.com/docs/api/object-storage/#object-storage-object-acl-config-update

        :param cluster_id: The ID of the cluster this bucket exists in.
        :type cluster_id: str

        :param bucket: The bucket name.
        :type bucket: str

        :param acl:
            Enum: private public-read authenticated-read public-read-write custom
            The Access Control Level of the bucket, as a canned ACL string.
            For more fine-grained control of ACLs, use the S3 API directly.
        :type acl: str

        :param name: The name of the object for which to retrieve its Access Control 
                     List (ACL). Use the Object Storage Bucket Contents List endpoint 
                     to access all object names in a bucket.
        :type name: str

        :returns: The Object's canned ACL and policy.
        :rtype: dict {acl: str, acl_xml: str}
            :acl:
                Enum: private public-read authenticated-read public-read-write custom
                The Access Control Level of the bucket, as a canned ACL string.
                For more fine-grained control of ACLs, use the S3 API directly.
            :acl_xml:
                The full XML of the object’s ACL policy.
        """
        params = {
            "acl": acl,
            "name": name,
        }

        result = self.client.put(
            "/object-storage/buckets/{}/{}/object-acl".format(
                cluster_id, bucket
            ),
            data=params,
        )

        if "errors" in result:
            raise UnexpectedResponseError(
                "Unexpected response when updating Object’s configured ACL!",
                json=result,
            )

        return MappedObject(**result)

    def bucket_contents(
        self,
        cluster_id,
        bucket,
        marker=None,
        delimiter=None,
        prefix=None,
        page_size=100,
    ):
        """
        Returns the contents of a bucket.
        The contents are paginated using a marker, which is the name of the last object 
        on the previous page. Objects may be filtered by prefix and delimiter as well; 
        see Query Parameters for more information.

        This endpoint is available for convenience.
        It is recommended that instead you use the more fully-featured S3 API directly.

        API Documentation: https://www.linode.com/docs/api/object-storage/#object-storage-bucket-contents-list

        :param cluster_id: The ID of the cluster this bucket exists in.
        :type cluster_id: str

        :param bucket: The bucket name.
        :type bucket: str

        :param marker: The “marker” for this request, which can be used to paginate 
                       through large buckets. Its value should be the value of the 
                       next_marker property returned with the last page. Listing 
                       bucket contents does not support arbitrary page access. See the 
                       next_marker property in the responses section for more details.
        :type marker: str

        :param delimiter: The delimiter for object names; if given, object names will 
                          be returned up to the first occurrence of this character. 
                          This is most commonly used with the / character to allow 
                          bucket transversal in a manner similar to a filesystem, 
                          however any delimiter may be used. Use in conjunction with 
                          prefix to see object names past the first occurrence of 
                          the delimiter.
        :type delimiter: str

        :param prefix: Filters objects returned to only those whose name start with 
                       the given prefix. Commonly used in conjunction with delimiter 
                       to allow transversal of bucket contents in a manner similar to 
                       a filesystem.
        :type perfix: str

        :param page_size: The number of items to return per page. Defaults to 100.
        :type page_size: integer 25..500

        :returns: One page of the requested bucket's contents.
        :rtype:
            [{
                etag: str,
                is_truncated: boolean,
                last_modified: string<date-time>,
                name: str,
                next_marker: str,
                owner: str,
                size: integer,
            }]
            :etag: An MD-5 hash of the object. null if this object represents a prefix.
            :is_truncated: Designates if there is another page of bucket objects.
            :last_modified: The date and time this object was last modified. 
                            null if this object represents a prefix.
            :name: The name of this object or prefix.
            :next_marker: Returns the value you should pass to the marker query 
                          parameter to get the next page of objects. 
                          If there is no next page, null will be returned.
            :owner: The owner of this object, as a UUID. null if this object 
                    represents a prefix.
            :size: The size of this object, in bytes. null if this object represents 
                   a prefix.
        """
        params = {
            "marker": marker,
            "delimiter": delimiter,
            "prefix": prefix,
            "page_size": page_size,
        }
        result = self.client.get(
            "/object-storage/buckets/{}/{}/object-list".format(
                cluster_id, bucket
            ),
            data=drop_null_keys(params),
        )

        if "errors" in result:
            raise UnexpectedResponseError(
                "Unexpected response when getting the contents of a bucket!",
                json=result,
            )

        return [MappedObject(**c) for c in result["data"]]

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
        :type expires_in: integer 360..86400

        :param method: The HTTP method allowed to be used with the pre-signed URL.
        :type method: str

        :param name: The name of the object that will be accessed with the pre-signed 
                     URL. This object need not exist, and no error will be returned 
                     if it doesn’t. This behavior is useful for generating pre-signed 
                     URLs to upload new objects to by setting the method to “PUT”.
        :type name: str

        :returns: The signed URL to perform the request at.
        :rtype: str
        """
        if method not in ("GET", "DELETE") and content_type is None:
            raise ValueError(
                "Content-type header is missing for the current method!"
            )
        params = {
            'method': method,
            'name': name,
            'expires_in': expires_in,
            'content_type': content_type,
        }

        result = self.client.post(
            "/object-storage/buckets/{}/{}/object-url".format(
                cluster_id, bucket
            ),
            data=drop_null_keys(params),
        )

        if "errors" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating the access url of an object!",
                json=result,
            )
        
        return MappedObject(**result)

    def ssl_cert_delete(self, cluster_id, bucket):
        """
        Deletes this Object Storage bucket’s user uploaded TLS/SSL certificate 
        and private key.

        API Documentation: https://www.linode.com/docs/api/object-storage/#object-storage-tlsssl-cert-delete

        :param cluster_id: The ID of the cluster this bucket exists in.
        :type cluster_id: str

        :param bucket: The bucket name.
        :type bucket: str
        """

        resp = self.client.delete("/object-storage/buckets/{}/{}/ssl".format(cluster_id, bucket))

        if "errors" in resp:
            raise UnexpectedResponseError(
                "Unexpected response when deleting a bucket!",
                json=resp,
            )
        return True

    def ssl_cert(self, cluster_id, bucket):
        """
        Returns a boolean value indicating if this bucket has a corresponding 
        TLS/SSL certificate that was uploaded by an Account user.

        API Documentation: https://www.linode.com/docs/api/object-storage/#object-storage-tlsssl-cert-view

        :param cluster_id: The ID of the cluster this bucket exists in.
        :type cluster_id: str

        :param bucket: The bucket name.
        :type bucket: str

        :returns: A boolean indicating if this Bucket has a corresponding 
                  TLS/SSL certificate that was uploaded by an Account user.
        :rtype: boolean
        """
        result = self.client.get("/object-storage/buckets/{}/{}/ssl".format(cluster_id, bucket))

        if "errors" in result:
            raise UnexpectedResponseError(
                "Unexpected response when getting the TLS/SSL certs indicator of a bucket!",
                json=result,
            )

        return MappedObject(**result)

    def ssl_cert_upload(self, cluster_id, bucket, certificate, private_key):
        """
        Upload a TLS/SSL certificate and private key to be served when you 
        visit your Object Storage bucket via HTTPS. Your TLS/SSL certificate and 
        private key are stored encrypted at rest.

        To replace an expired certificate, delete your current certificate and 
        upload a new one.

        API Documentation: https://www.linode.com/docs/api/object-storage/#object-storage-tlsssl-cert-upload

        :param cluster_id: The ID of the cluster this bucket exists in.
        :type cluster_id: str

        :param bucket: The bucket name.
        :type bucket: str

        :param certificate: Your Base64 encoded and PEM formatted SSL certificate.
                            Line breaks must be represented as “\n” in the string 
                            for requests (but not when using the Linode CLI)
        :type certificate: str

        :param private_key: The private key associated with this TLS/SSL certificate.
                            Line breaks must be represented as “\n” in the string 
                            for requests (but not when using the Linode CLI)
        :type private_key: str

        :returns: A boolean indicating if this Bucket has a corresponding 
                  TLS/SSL certificate that was uploaded by an Account user.
        :rtype: boolean
        """
        params ={
            "certificate": certificate,
            "private_key": private_key,
        }
        result = self.client.post(
            "/object-storage/buckets/{}/{}/ssl".format(cluster_id, bucket),
            data=params,
        )

        if "errors" in result:
            raise UnexpectedResponseError(
                "Unexpected response when uploading TLS/SSL certs!",
                json=result,
            )

        return MappedObject(**result)

class LinodeClient:
    def __init__(
        self,
        token,
        base_url="https://api.linode.com/v4",
        user_agent=None,
        page_size=None,
        retry_rate_limit_interval=None,
    ):
        """
        The main interface to the Linode API.

        :param token: The authentication token to use for communication with the
                      API.  Can be either a Personal Access Token or an OAuth Token.
        :type token: str
        :param base_url: The base URL for API requests.  Generally, you shouldn't
                         change this.
        :type base_url: str
        :param user_agent: What to append to the User Agent of all requests made
                           by this client.  Setting this allows Linode's internal
                           monitoring applications to track the usage of your
                           application.  Setting this is not necessary, but some
                           applications may desire this behavior.
        :type user_agent: str
        :param page_size: The default size to request pages at.  If not given,
                                  the API's default page size is used.  Valid values
                                  can be found in the API docs, but at time of writing
                                  are between 25 and 500.
        :type page_size: int
        :param retry_rate_limit_interval: If given, 429 responses will be automatically
                                         retried up to 5 times with the given interval,
                                         in seconds, between attempts.
        :type retry_rate_limit_interval: int
        """
        self.base_url = base_url
        self._add_user_agent = user_agent
        self.token = token
        self.session = requests.Session()
        self.page_size = page_size
        self.retry_rate_limit_interval = retry_rate_limit_interval

        # make sure we got a sane backoff
        if self.retry_rate_limit_interval is not None:
            if not isinstance(self.retry_rate_limit_interval, int):
                raise ValueError("retry_rate_limit_interval must be an int")
            if self.retry_rate_limit_interval < 1:
                raise ValueError(
                    "retry_rate_limit_interval must not be less than 1"
                )

        #: Access methods related to Linodes - see :any:`LinodeGroup` for
        #: more information
        self.linode = LinodeGroup(self)

        #: Access methods related to your user - see :any:`ProfileGroup` for
        #: more information
        self.profile = ProfileGroup(self)

        #: Access methods related to your account - see :any:`AccountGroup` for
        #: more information
        self.account = AccountGroup(self)

        #: Access methods related to networking on your account - see
        #: :any:`NetworkingGroup` for more information
        self.networking = NetworkingGroup(self)

        #: Access methods related to support - see :any:`SupportGroup` for more
        #: information
        self.support = SupportGroup(self)

        #: Access information related to the Longview service - see
        #: :any:`LongviewGroup` for more information
        self.longview = LongviewGroup(self)

        #: Access methods related to Object Storage - see :any:`ObjectStorageGroup`
        #: for more information
        self.object_storage = ObjectStorageGroup(self)

        #: Access methods related to LKE - see :any:`LKEGroup` for more information.
        self.lke = LKEGroup(self)

        #: Access methods related to Managed Databases - see :any:`DatabaseGroup` for more information.
        self.database = DatabaseGroup(self)

        #: Access methods related to NodeBalancers - see :any:`NodeBalancerGroup` for more information.
        self.nodebalancers = NodeBalancerGroup(self)

        #: Access methods related to Domains - see :any:`DomainGroup` for more information.
        self.domains = DomainGroup(self)

        #: Access methods related to Tags - See :any:`TagGroup` for more information.
        self.tags = TagGroup(self)

        #: Access methods related to Volumes - See :any:`VolumeGroup` for more information.
        self.volumes = VolumeGroup(self)

        #: Access methods related to Regions - See :any:`RegionGroup` for more information.
        self.regions = RegionGroup(self)

        #: Access methods related to Images - See :any:`ImageGroup` for more information.
        self.images = ImageGroup(self)

    @property
    def _user_agent(self):
        return "{}python-linode_api4/{} {}".format(
            "{} ".format(self._add_user_agent) if self._add_user_agent else "",
            package_version,
            requests.utils.default_user_agent(),
        )

    def load(self, target_type, target_id, target_parent_id=None):
        """
        Constructs and immediately loads the object, circumventing the
        lazy-loading scheme by immediately making an API request.  Does not
        load related objects.

        For example, if you wanted to load an :any:`Instance` object with ID 123,
        you could do this::

           loaded_linode = client.load(Instance, 123)

        Similarly, if you instead wanted to load a :any:`NodeBalancerConfig`,
        you could do so like this::

           loaded_nodebalancer_config = client.load(NodeBalancerConfig, 456, 432)

        :param target_type: The type of object to create.
        :type target_type: type
        :param target_id: The ID of the object to create.
        :type target_id: int or str
        :param target_parent_id: The parent ID of the object to create, if
                                 applicable.
        :type target_parent_id: int, str, or None

        :returns: The resulting object, fully loaded.
        :rtype: target_type
        :raise ApiError: if the requested object could not be loaded.
        """
        result = target_type.make_instance(
            target_id, self, parent_id=target_parent_id
        )
        result._api_get()

        return result

    def _api_call(
        self, endpoint, model=None, method=None, data=None, filters=None
    ):
        """
        Makes a call to the linode api.  Data should only be given if the method is
        POST or PUT, and should be a dictionary
        """
        if not self.token:
            raise RuntimeError("You do not have an API token!")

        if not method:
            raise ValueError("Method is required for API calls!")

        if model:
            endpoint = endpoint.format(**vars(model))
        url = "{}{}".format(self.base_url, endpoint)
        headers = {
            "Authorization": "Bearer {}".format(self.token),
            "Content-Type": "application/json",
            "User-Agent": self._user_agent,
        }

        if filters:
            headers["X-Filter"] = json.dumps(filters)

        body = None
        if data is not None:
            body = json.dumps(data)

        # retry on 429 response
        max_retries = 5 if self.retry_rate_limit_interval else 1
        for attempt in range(max_retries):
            response = method(url, headers=headers, data=body)

            warning = response.headers.get("Warning", None)
            if warning:
                logger.warning(
                    "Received warning from server: {}".format(warning)
                )

            # if we were configured to retry 429s, and we got a 429, sleep briefly and then retry
            if self.retry_rate_limit_interval and response.status_code == 429:
                logger.warning(
                    "Received 429 response; waiting {} seconds and retrying request (attempt {}/{})".format(
                        self.retry_rate_limit_interval,
                        attempt,
                        max_retries,
                    )
                )
                time.sleep(self.retry_rate_limit_interval)
            else:
                break

        if 399 < response.status_code < 600:
            j = None
            error_msg = "{}: ".format(response.status_code)
            try:
                j = response.json()
                if "errors" in j.keys():
                    for e in j["errors"]:
                        msg = e.get("reason", "")
                        field = e.get("field", None)

                        error_msg += "{}{}; ".format(
                            f"[{field}] " if field is not None else "",
                            msg,
                        )
            except:
                pass
            raise ApiError(error_msg, status=response.status_code, json=j)

        if response.status_code != 204:
            j = response.json()
        else:
            j = None  # handle no response body

        return j

    def _get_objects(
        self, endpoint, cls, model=None, parent_id=None, filters=None
    ):
        # handle non-default page sizes
        call_endpoint = endpoint
        if self.page_size is not None:
            call_endpoint += "?page_size={}".format(self.page_size)

        response_json = self.get(call_endpoint, model=model, filters=filters)

        if not "data" in response_json:
            raise UnexpectedResponseError(
                "Problem with response!", json=response_json
            )

        if "pages" in response_json:
            formatted_endpoint = endpoint
            if model:
                formatted_endpoint = formatted_endpoint.format(**vars(model))
            return PaginatedList.make_paginated_list(
                response_json,
                self,
                cls,
                parent_id=parent_id,
                page_url=formatted_endpoint[1:],
                filters=filters,
            )
        return PaginatedList.make_list(
            response_json["data"], self, cls, parent_id=parent_id
        )

    def get(self, *args, **kwargs):
        return self._api_call(*args, method=self.session.get, **kwargs)

    def post(self, *args, **kwargs):
        return self._api_call(*args, method=self.session.post, **kwargs)

    def put(self, *args, **kwargs):
        return self._api_call(*args, method=self.session.put, **kwargs)

    def delete(self, *args, **kwargs):
        return self._api_call(*args, method=self.session.delete, **kwargs)

    def image_create(self, disk, label=None, description=None):
        """
        .. note:: This method is an alias to maintain backwards compatibility.
                  Please use :meth:`LinodeClient.images.create(...) <.ImageGroup.create>` for all new projects.
        """
        return self.images.create(disk, label=label, description=description)

    def image_create_upload(
        self, label: str, region: str, description: str = None
    ) -> Tuple[Image, str]:
        """
        .. note:: This method is an alias to maintain backwards compatibility.
                  Please use :meth:`LinodeClient.images.create_upload(...) <.ImageGroup.create_upload>`
                  for all new projects.
        """

        return self.images.create_upload(label, region, description=description)

    def image_upload(
        self, label: str, region: str, file: BinaryIO, description: str = None
    ) -> Image:
        """
        .. note:: This method is an alias to maintain backwards compatibility.
                  Please use :meth:`LinodeClient.images.upload(...) <.ImageGroup.upload>` for all new projects.
        """
        return self.images.upload(label, region, file, description=description)

    def nodebalancer_create(self, region, **kwargs):
        """
        .. note:: This method is an alias to maintain backwards compatibility.
                  Please use
                  :meth:`LinodeClient.nodebalancers.create(...) <.NodeBalancerGroup.create>`
                  for all new projects.
        """
        return self.nodebalancers.create(region, **kwargs)

    def domain_create(self, domain, master=True, **kwargs):
        """
        .. note:: This method is an alias to maintain backwards compatibility.
                  Please use :meth:`LinodeClient.domains.create(...) <.DomainGroup.create>` for all
                  new projects.
        """
        return self.domains.create(domain, master=master, **kwargs)

    def tag_create(
        self,
        label,
        instances=None,
        domains=None,
        nodebalancers=None,
        volumes=None,
        entities=[],
    ):
        """
        .. note:: This method is an alias to maintain backwards compatibility.
                  Please use :meth:`LinodeClient.tags.create(...) <.TagGroup.create>` for all new projects.
        """
        return self.tags.create(
            label,
            instances=instances,
            domains=domains,
            nodebalancers=nodebalancers,
            volumes=volumes,
            entities=entities,
        )

    def volume_create(self, label, region=None, linode=None, size=20, **kwargs):
        """
        .. note:: This method is an alias to maintain backwards compatibility.
                  Please use :meth:`LinodeClient.volumes.create(...) <.VolumeGroup.create>` for all new projects.
        """
        return self.volumes.create(
            label, region=region, linode=linode, size=size, **kwargs
        )

    # helper functions
    def _get_and_filter(self, obj_type, *filters, endpoint=None):
        parsed_filters = None
        if filters:
            if len(filters) > 1:
                parsed_filters = and_(
                    *filters
                ).dct  # pylint: disable=no-value-for-parameter
            else:
                parsed_filters = filters[0].dct

        # Use sepcified endpoint
        if endpoint:
            return self._get_objects(endpoint, obj_type, filters=parsed_filters)
        else:
            return self._get_objects(
                obj_type.api_list(), obj_type, filters=parsed_filters
            )

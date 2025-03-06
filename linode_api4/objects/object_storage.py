from dataclasses import dataclass
from typing import Optional
from urllib import parse

from deprecated import deprecated

from linode_api4.common import Price, RegionPrice
from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects import (
    Base,
    DerivedBase,
    MappedObject,
    Property,
    Region,
)
from linode_api4.objects.serializable import JSONObject, StrEnum
from linode_api4.util import drop_null_keys


class ObjectStorageACL(StrEnum):
    PRIVATE = "private"
    PUBLIC_READ = "public-read"
    AUTHENTICATED_READ = "authenticated-read"
    PUBLIC_READ_WRITE = "public-read-write"
    CUSTOM = "custom"


class ObjectStorageKeyPermission(StrEnum):
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"


class ObjectStorageEndpointType(StrEnum):
    E0 = "E0"
    E1 = "E1"
    E2 = "E2"
    E3 = "E3"


@dataclass
class ObjectStorageEndpoint(JSONObject):
    """
    ObjectStorageEndpoint contains the core fields of an object storage endpoint object.

    NOTE: This is not implemented as a typical API object (Base) because Object Storage Endpoints
    cannot be refreshed, as there is no singular GET endpoint.
    """

    region: str = ""
    endpoint_type: ObjectStorageEndpointType = ""
    s3_endpoint: Optional[str] = None


class ObjectStorageType(Base):
    """
    An ObjectStorageType represents the structure of a valid Object Storage type.
    Currently, the ObjectStorageType can only be retrieved by listing, i.e.:
        types = client.object_storage.types()

    API documentation: https://techdocs.akamai.com/linode-api/reference/get-object-storage-types
    """

    properties = {
        "id": Property(identifier=True),
        "label": Property(),
        "price": Property(json_object=Price),
        "region_prices": Property(json_object=RegionPrice),
        "transfer": Property(),
    }


class ObjectStorageBucket(DerivedBase):
    """
    A bucket where objects are stored in.

    API documentation: https://techdocs.akamai.com/linode-api/reference/get-object-storage-bucket
    """

    api_endpoint = "/object-storage/buckets/{region}/{label}"
    parent_id_name = "region"
    id_attribute = "label"

    properties = {
        "region": Property(identifier=True),
        "cluster": Property(),
        "created": Property(is_datetime=True),
        "hostname": Property(),
        "label": Property(identifier=True),
        "objects": Property(),
        "size": Property(),
        "endpoint_type": Property(),
        "s3_endpoint": Property(),
    }

    @classmethod
    def api_list(cls):
        """
        Override this method to return the correct URL that will produce
        a list of JSON objects of this class' type - Object Storage Bucket.
        """
        return "/".join(cls.api_endpoint.split("/")[:-2])

    @classmethod
    def make_instance(cls, id, client, parent_id=None, json=None):
        """
        Override this method to pass in the parent_id from the _raw_json object
        when it's available.
        """
        if json is not None:
            parent_id = parent_id or json.get("region") or json.get("cluster")

        if parent_id:
            return super().make(id, client, cls, parent_id=parent_id, json=json)
        else:
            raise UnexpectedResponseError(
                "Unexpected json response when making a new Object Storage Bucket instance."
            )

    def access_get(self):
        """
        Returns a result object which wraps the current access config for this ObjectStorageBucket.

        API Documentation: TODO

        :returns: A result object which wraps the access that this ObjectStorageBucket is currently configured with.
        :rtype: MappedObject
        """
        result = self._client.get(
            "{}/access".format(self.api_endpoint),
            model=self,
        )

        if not any(
            key in result
            for key in ["acl", "acl_xml", "cors_enabled", "cors_xml"]
        ):
            raise UnexpectedResponseError(
                "Unexpected response when getting the bucket access config of a bucket!",
                json=result,
            )

        return MappedObject(**result)

    def access_modify(
        self,
        acl: Optional[ObjectStorageACL] = None,
        cors_enabled=None,
    ):
        """
        Allows changing basic Cross-origin Resource Sharing (CORS) and Access Control
        Level (ACL) settings. Only allows enabling/disabling CORS for all origins,
        and/or setting canned ACLs. For more fine-grained control of both systems,
        please use the more fully-featured S3 API directly.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-object-storage-bucket-access

        :param acl: The Access Control Level of the bucket using a canned ACL string.
                    For more fine-grained control of ACLs, use the S3 API directly.
        :type acl: str
                   Enum: private,public-read,authenticated-read,public-read-write

        :param cors_enabled: If true, the bucket will be created with CORS enabled for
                             all origins. For more fine-grained controls of CORS, use
                             the S3 API directly.
        :type cors_enabled: bool
        """
        params = {
            "acl": acl,
            "cors_enabled": cors_enabled,
        }

        resp = self._client.post(
            f"{self.api_endpoint}/access",
            data=drop_null_keys(params),
            model=self,
        )

        if "errors" in resp:
            raise UnexpectedResponseError(
                "Unexpected response when modifying the access to a bucket!",
                json=resp,
            )
        return True

    def access_update(
        self,
        acl: Optional[ObjectStorageACL] = None,
        cors_enabled=None,
    ):
        """
        Allows changing basic Cross-origin Resource Sharing (CORS) and Access Control
        Level (ACL) settings. Only allows enabling/disabling CORS for all origins,
        and/or setting canned ACLs. For more fine-grained control of both systems,
        please use the more fully-featured S3 API directly.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/put-storage-bucket-access

        :param acl: The Access Control Level of the bucket using a canned ACL string.
                    For more fine-grained control of ACLs, use the S3 API directly.
        :type acl: str
                   Enum: private,public-read,authenticated-read,public-read-write

        :param cors_enabled: If true, the bucket will be created with CORS enabled for
                             all origins. For more fine-grained controls of CORS,
                             use the S3 API directly.
        :type cors_enabled: bool
        """
        params = {
            "acl": acl,
            "cors_enabled": cors_enabled,
        }

        resp = self._client.put(
            f"{self.api_endpoint}/access",
            data=drop_null_keys(params),
            model=self,
        )

        if "errors" in resp:
            raise UnexpectedResponseError(
                "Unexpected response when updating the access to a bucket!",
                json=resp,
            )
        return True

    def ssl_cert_delete(self):
        """
        Deletes this Object Storage bucket’s user uploaded TLS/SSL certificate
        and private key.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/delete-object-storage-ssl

        :returns: True if the TLS/SSL certificate and private key in the bucket were successfully deleted.
        :rtype: bool
        """

        resp = self._client.delete(
            f"{self.api_endpoint}/ssl",
            model=self,
        )

        if "error" in resp:
            raise UnexpectedResponseError(
                "Unexpected response when deleting a bucket!",
                json=resp,
            )
        return True

    def ssl_cert(self):
        """
        Returns a result object which wraps a bool value indicating
        if this bucket has a corresponding TLS/SSL certificate that
        was uploaded by an Account user.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-object-storage-ssl

        :returns: A result object which has a bool field indicating if this Bucket has a corresponding
                  TLS/SSL certificate that was uploaded by an Account user.
        :rtype: MappedObject
        """
        result = self._client.get(
            f"{self.api_endpoint}/ssl",
            model=self,
        )

        if not "ssl" in result:
            raise UnexpectedResponseError(
                "Unexpected response when getting the TLS/SSL certs indicator of a bucket!",
                json=result,
            )

        return MappedObject(**result)

    def ssl_cert_upload(self, certificate, private_key):
        """
        Upload a TLS/SSL certificate and private key to be served when you
        visit your Object Storage bucket via HTTPS. Your TLS/SSL certificate and
        private key are stored encrypted at rest.

        To replace an expired certificate, delete your current certificate and
        upload a new one.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-object-storage-ssl

        :param certificate: Your Base64 encoded and PEM formatted SSL certificate.
                            Line breaks must be represented as “\n” in the string
                            for requests (but not when using the Linode CLI)
        :type certificate: str

        :param private_key: The private key associated with this TLS/SSL certificate.
                            Line breaks must be represented as “\n” in the string
                            for requests (but not when using the Linode CLI)
        :type private_key: str

        :returns: A result object which has a bool field indicating if this Bucket has a corresponding
                  TLS/SSL certificate that was uploaded by an Account user.
        :rtype: MappedObject
        """
        params = {
            "certificate": certificate,
            "private_key": private_key,
        }
        result = self._client.post(
            f"{self.api_endpoint}/ssl",
            data=params,
            model=self,
        )

        if not "ssl" in result:
            raise UnexpectedResponseError(
                "Unexpected response when uploading TLS/SSL certs!",
                json=result,
            )

        return MappedObject(**result)

    def contents(
        self,
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

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-object-storage-bucket-content

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
        :type page_size: int 25..500

        :returns: A list of the MappedObject of the requested bucket's contents.
        :rtype: [MappedObject]
        """
        params = {
            "marker": marker,
            "delimiter": delimiter,
            "prefix": prefix,
            "page_size": page_size,
        }
        result = self._client.get(
            f"{self.api_endpoint}/object-list",
            data=drop_null_keys(params),
            model=self,
        )

        if not "data" in result:
            raise UnexpectedResponseError(
                "Unexpected response when getting the contents of a bucket!",
                json=result,
            )

        return [MappedObject(**c) for c in result["data"]]

    def object_acl_config(self, name=None):
        """
        View an Object’s configured Access Control List (ACL) in this Object Storage
        bucket. ACLs define who can access your buckets and objects and specify the
        level of access granted to those users.

        This endpoint is available for convenience.
        It is recommended that instead you use the more fully-featured S3 API directly.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-object-storage-bucket-acl

        :param name: The name of the object for which to retrieve its Access Control
                     List (ACL). Use the Object Storage Bucket Contents List endpoint
                     to access all object names in a bucket.
        :type name: str

        :returns: The Object's canned ACL and policy.
        :rtype: MappedObject
        """
        params = {
            "name": name,
        }

        result = self._client.get(
            f"{type(self).api_endpoint}/object-acl",
            model=self,
            data=drop_null_keys(params),
        )

        if not "acl" in result:
            raise UnexpectedResponseError(
                "Unexpected response when viewing Object’s configured ACL!",
                json=result,
            )

        return MappedObject(**result)

    def object_acl_config_update(self, acl: ObjectStorageACL, name):
        """
        Update an Object’s configured Access Control List (ACL) in this Object Storage
        bucket. ACLs define who can access your buckets and objects and specify the
        level of access granted to those users.

        This endpoint is available for convenience.
        It is recommended that instead you use the more fully-featured S3 API directly.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/put-object-storage-bucket-acl

        :param acl: The Access Control Level of the bucket, as a canned ACL string.
                    For more fine-grained control of ACLs, use the S3 API directly.
        :type acl: str
                   Enum: private,public-read,authenticated-read,public-read-write,custom

        :param name: The name of the object for which to retrieve its Access Control
                     List (ACL). Use the Object Storage Bucket Contents List endpoint
                     to access all object names in a bucket.
        :type name: str

        :returns: The Object's canned ACL and policy.
        :rtype: MappedObject
        """
        params = {
            "acl": acl,
            "name": name,
        }

        result = self._client.put(
            f"{type(self).api_endpoint}/object-acl",
            model=self,
            data=params,
        )

        if not "acl" in result:
            raise UnexpectedResponseError(
                "Unexpected response when updating Object’s configured ACL!",
                json=result,
            )

        return MappedObject(**result)

    @deprecated(
        reason=(
            "'access' method has been deprecated in favor of the class method "
            "'bucket_access' in ObjectStorageGroup, which can be accessed by "
            "'client.object_storage.access'"
        )
    )
    def access(self, cluster, bucket_name, permissions):
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

        :returns: A dict formatted correctly for specifying bucket access for
                  new keys.
        :rtype: dict
        """
        return {
            "cluster": cluster,
            "bucket_name": bucket_name,
            "permissions": permissions,
        }


@deprecated(
    reason="deprecated to use regions list API for viewing available OJB clusters"
)
class ObjectStorageCluster(Base):
    """
    This class will be deprecated to use the regions list to view available OBJ clusters,
    and a new access key API will directly expose the S3 endpoint hostname.

    A cluster where Object Storage is available.

    API documentation: https://techdocs.akamai.com/linode-api/reference/get-object-storage-cluster
    """

    api_endpoint = "/object-storage/clusters/{id}"

    properties = {
        "id": Property(identifier=True),
        "region": Property(slug_relationship=Region),
        "status": Property(),
        "domain": Property(),
        "static_site_domain": Property(),
    }

    @deprecated(
        reason=(
            "'buckets_in_cluster' method has been deprecated, please consider "
            "switching to 'buckets_in_region' in the object storage group (can "
            "be accessed via 'client.object_storage.buckets_in_cluster')."
        )
    )
    def buckets_in_cluster(self, *filters):
        """
        Returns a list of Buckets in this cluster belonging to this Account.

        This endpoint is available for convenience.
        It is recommended that instead you use the more fully-featured S3 API directly.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-object-storage-bucketin-cluster

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Object Storage Buckets that in the requested cluster.
        :rtype: PaginatedList of ObjectStorageBucket
        """

        return self._client._get_and_filter(
            ObjectStorageBucket,
            *filters,
            endpoint="/object-storage/buckets/{}".format(
                parse.quote(str(self.id))
            ),
        )


class ObjectStorageKeys(Base):
    """
    A keypair that allows third-party applications to access Linode Object Storage.

    API documentation: https://techdocs.akamai.com/linode-api/reference/get-object-storage-key
    """

    api_endpoint = "/object-storage/keys/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True),
        "access_key": Property(),
        "secret_key": Property(),
        "bucket_access": Property(),
        "limited": Property(),
        "regions": Property(unordered=True),
    }

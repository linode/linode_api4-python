from enum import StrEnum

from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects import Base, DerivedBase, Property, Region
from linode_api4.util import drop_null_keys


class BucketACL(StrEnum):
    """
    BucketACL StrEnum represents the access control level of a object storage bucket.
    """
    PRIVATE = "private"
    PUBLIC_READ = "public-read"
    AUTHENTICAED_READ = "authenticated-read"
    PUBLIC_READ_WRITE = "public-read-write"

class ObjectStorageBucket(DerivedBase):
    """
    A bucket where objects are stored in.
    """

    api_endpoint = "/object-storage/buckets/{cluster}/{label}"
    parent_id_name = "cluster"
    id_attribute = "label"

    properties = {
        "cluster": Property(),
        "created": Property(is_datetime=True),
        "hostname": Property(),
        "label": Property(),
        "objects": Property(),
        "size": Property(),
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
        if json is None:
            return None
        if parent_id is None and json["cluster"]:
            parent_id = json["cluster"]

        if parent_id:
            return Base.make(id, client, cls, parent_id=parent_id, json=json)
        else:
            raise UnexpectedResponseError(
                "Unexpected json response when making a new Object Storage Bucket instance."
            )

    def access_modify(
        self, cluster_id, bucket, acl : BucketACL = None, cors_enabled=None
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
        :type acl: BucketACL

        :param cors_enabled: If true, the bucket will be created with CORS enabled for
                             all origins. For more fine-grained controls of CORS, use
                             the S3 API directly.
        :type cors_enabled: boolean
        """
        params = {
            "acl": acl,
            "cors_enabled": cors_enabled,
        }

        resp = self._client.post(
            "/object-storage/buckets/{}/{}/access".format(cluster_id, bucket),
            data=drop_null_keys(params),
        )

        if "errors" in resp:
            raise UnexpectedResponseError(
                "Unexpected response when modifying the access to a bucket!",
                json=resp,
            )
        return True

    def access_update(
        self, cluster_id, bucket, acl : BucketACL = None, cors_enabled=None
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
        :type acl: BucketACL

        :param cors_enabled: If true, the bucket will be created with CORS enabled for
                             all origins. For more fine-grained controls of CORS,
                             use the S3 API directly.
        :type cors_enabled: boolean
        """
        params = {
            "acl": acl,
            "cors_enabled": cors_enabled,
        }

        resp = self._client.put(
            "/object-storage/buckets/{}/{}/access".format(cluster_id, bucket),
            data=drop_null_keys(params),
        )

        if "errors" in resp:
            raise UnexpectedResponseError(
                "Unexpected response when updating the access to a bucket!",
                json=resp,
            )
        return True

class ObjectStorageCluster(Base):
    """
    A cluster where Object Storage is available.
    """

    api_endpoint = "/object-storage/clusters/{id}"

    properties = {
        "id": Property(identifier=True),
        "region": Property(slug_relationship=Region),
        "status": Property(),
        "domain": Property(),
        "static_site_domain": Property(),
    }


class ObjectStorageKeys(Base):
    """
    A keypair that allows third-party applications to access Linode Object Storage.
    """

    api_endpoint = "/object-storage/keys/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True),
        "access_key": Property(),
        "secret_key": Property(),
        "bucket_access": Property(),
        "limited": Property(),
    }

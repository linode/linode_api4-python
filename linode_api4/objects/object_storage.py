from linode_api4.objects import Base, DerivedBase, Property, Region
from linode_api4.errors import UnexpectedResponseError


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

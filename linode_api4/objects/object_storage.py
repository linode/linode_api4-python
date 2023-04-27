from linode_api4.objects import Base, DerivedBase, Image, Property, Region


class ObjectStorageCluster(Base):
    """
    A cluster where Object Storage is available.

    API documentation: https://www.linode.com/docs/api/object-storage/#cluster-view
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

    API documentation: https://www.linode.com/docs/api/object-storage/#object-storage-key-view
    """

    api_endpoint = "/object-storage/keys/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True),
        "access_key": Property(),
        "secret_key": Property(),
    }

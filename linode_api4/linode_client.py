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
    available clusters and managing keys.
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


class DatabaseGroup(Group):
    """
    Encapsulates Linode Managed Databases related methods of the :any:`LinodeClient`. This
    should not be instantiated on its own, but should instead be used through
    an instance of :any:`LinodeClient`::

       client = LinodeClient(token)
       instances = client.database.instances() # use the DatabaseGroup

    This group contains all features beneath the `/databases` group in the API v4.
    """

    def types(self, *filters):
        """
        Returns a list of Linode Database-compatible Instance types.
        These may be used to create Managed Databases, or simply
        referenced to on their own. DatabaseTypes can be
        filtered to return specific types, for example::

           database_types = client.database.types(DatabaseType.deprecated == False)

        API Documentation: https://www.linode.com/docs/api/databases/#managed-database-types-list

        :param filters: Any number of filters to apply to the query.

        :returns: A list of types that match the query.
        :rtype: PaginatedList of DatabaseType
        """
        return self.client._get_and_filter(DatabaseType, *filters)

    def engines(self, *filters):
        """
        Returns a list of Linode Managed Database Engines.
        These may be used to create Managed Databases, or simply
        referenced to on their own. Engines can be filtered to
        return specific engines, for example::

           mysql_engines = client.database.engines(DatabaseEngine.engine == 'mysql')

        API Documentation: https://www.linode.com/docs/api/databases/#managed-database-engines-list

        :param filters: Any number of filters to apply to the query.

        :returns: A list of types that match the query.
        :rtype: PaginatedList of DatabaseEngine
        """
        return self.client._get_and_filter(DatabaseEngine, *filters)

    def instances(self, *filters):
        """
        Returns a list of Managed Databases active on this account.

        API Documentation: https://www.linode.com/docs/api/databases/#managed-databases-list-all

        :param filters: Any number of filters to apply to this query.

        :returns: A list of databases that matched the query.
        :rtype: PaginatedList of Database
        """
        return self.client._get_and_filter(Database, *filters)

    def mysql_instances(self, *filters):
        """
        Returns a list of Managed MySQL Databases active on this account.

        API Documentation: https://www.linode.com/docs/api/databases/#managed-mysql-databases-list

        :param filters: Any number of filters to apply to this query.

        :returns: A list of MySQL databases that matched the query.
        :rtype: PaginatedList of MySQLDatabase
        """
        return self.client._get_and_filter(MySQLDatabase, *filters)

    def mysql_create(self, label, region, engine, ltype, **kwargs):
        """
        Creates an :any:`MySQLDatabase` on this account with
        the given label, region, engine, and node type.  For example::

           client = LinodeClient(TOKEN)

           # look up Region and Types to use.  In this example I'm just using
           # the first ones returned.
           region = client.regions().first()
           node_type = client.database.types()[0]
           engine = client.database.engines(DatabaseEngine.engine == 'mysql')[0]

           new_database = client.database.mysql_create(
               "example-database",
               region,
               engine.id,
               type.id
            )

        API Documentation: https://www.linode.com/docs/api/databases/#managed-mysql-database-create

        :param label: The name for this cluster
        :type label: str
        :param region: The region to deploy this cluster in
        :type region: str or Region
        :param engine: The engine to deploy this cluster with
        :type engine: str or Engine
        :param ltype: The Linode Type to use for this cluster
        :type ltype: str or Type
        """

        params = {
            "label": label,
            "region": region.id if issubclass(type(region), Base) else region,
            "engine": engine.id if issubclass(type(engine), Base) else engine,
            "type": ltype.id if issubclass(type(ltype), Base) else ltype,
        }
        params.update(kwargs)

        result = self.client.post("/databases/mysql/instances", data=params)

        if "id" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating MySQL Database", json=result
            )

        d = MySQLDatabase(self.client, result["id"], result)
        return d

    def postgresql_instances(self, *filters):
        """
        Returns a list of Managed PostgreSQL Databases active on this account.

        API Documentation: https://www.linode.com/docs/api/databases/#managed-postgresql-databases-list

        :param filters: Any number of filters to apply to this query.

        :returns: A list of PostgreSQL databases that matched the query.
        :rtype: PaginatedList of PostgreSQLDatabase
        """
        return self.client._get_and_filter(PostgreSQLDatabase, *filters)

    def postgresql_create(self, label, region, engine, ltype, **kwargs):
        """
        Creates an :any:`PostgreSQLDatabase` on this account with
        the given label, region, engine, and node type.  For example::

           client = LinodeClient(TOKEN)

           # look up Region and Types to use.  In this example I'm just using
           # the first ones returned.
           region = client.regions().first()
           node_type = client.database.types()[0]
           engine = client.database.engines(DatabaseEngine.engine == 'postgresql')[0]

           new_database = client.database.postgresql_create(
               "example-database",
               region,
               engine.id,
               type.id
            )

        API Documentation: https://www.linode.com/docs/api/databases/#managed-postgresql-database-create

        :param label: The name for this cluster
        :type label: str
        :param region: The region to deploy this cluster in
        :type region: str or Region
        :param engine: The engine to deploy this cluster with
        :type engine: str or Engine
        :param ltype: The Linode Type to use for this cluster
        :type ltype: str or Type
        """

        params = {
            "label": label,
            "region": region.id if issubclass(type(region), Base) else region,
            "engine": engine.id if issubclass(type(engine), Base) else engine,
            "type": ltype.id if issubclass(type(ltype), Base) else ltype,
        }
        params.update(kwargs)

        result = self.client.post(
            "/databases/postgresql/instances", data=params
        )

        if "id" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating PostgreSQL Database",
                json=result,
            )

        d = PostgreSQLDatabase(self.client, result["id"], result)
        return d

    def mongodb_instances(self, *filters):
        """
        Returns a list of Managed MongoDB Databases active on this account.

        API Documentation: https://www.linode.com/docs/api/databases/#managed-mongodb-databases-list

        :param filters: Any number of filters to apply to this query.

        :returns: A list of MongoDB databases that matched the query.
        :rtype: PaginatedList of MongoDBDatabase
        """
        return self.client._get_and_filter(MongoDBDatabase, *filters)

    def mongodb_create(self, label, region, engine, ltype, **kwargs):
        """
        Creates an :any:`MongoDBDatabase` on this account with
        the given label, region, engine, and node type.  For example::

           client = LinodeClient(TOKEN)

           # look up Region and Types to use.  In this example I'm just using
           # the first ones returned.
           region = client.regions().first()
           node_type = client.database.types()[0]
           engine = client.database.engines(DatabaseEngine.engine == 'mongodb')[0]

           new_database = client.database.mongodb_create(
               "example-database",
               region,
               engine.id,
               type.id
            )

        API Documentation: https://www.linode.com/docs/api/databases/#managed-mongodb-database-create

        :param label: The name for this cluster
        :type label: str
        :param region: The region to deploy this cluster in
        :type region: str or Region
        :param engine: The engine to deploy this cluster with
        :type engine: str or Engine
        :param ltype: The Linode Type to use for this cluster
        :type ltype: str or Type
        """

        params = {
            "label": label,
            "region": region.id if issubclass(type(region), Base) else region,
            "engine": engine.id if issubclass(type(engine), Base) else engine,
            "type": ltype.id if issubclass(type(ltype), Base) else ltype,
        }
        params.update(kwargs)

        result = self.client.post("/databases/mongodb/instances", data=params)

        if "id" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating MongoDB Database",
                json=result,
            )

        d = MongoDBDatabase(self.client, result["id"], result)
        return d


class NodeBalancerGroup(Group):
    def __call__(self, *filters):
        """
        Retrieves all of the NodeBalancers the acting user has access to.

        This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           nodebalancers = client.nodebalancers()

        API Documentation: https://www.linode.com/docs/api/nodebalancers/#nodebalancers-list

        :param filters: Any number of filters to apply to this query.

        :returns: A list of NodeBalancers the acting user can access.
        :rtype: PaginatedList of NodeBalancers
        """
        return self.client._get_and_filter(NodeBalancer, *filters)

    def create(self, region, **kwargs):
        """
        Creates a new NodeBalancer in the given Region.

        API Documentation: https://www.linode.com/docs/api/nodebalancers/#nodebalancer-create

        :param region: The Region in which to create the NodeBalancer.
        :type region: Region or str

        :returns: The new NodeBalancer
        :rtype: NodeBalancer
        """
        params = {
            "region": region.id if isinstance(region, Base) else region,
        }
        params.update(kwargs)

        result = self.client.post("/nodebalancers", data=params)

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating Nodebalaner!", json=result
            )

        n = NodeBalancer(self.client, result["id"], result)
        return n


class DomainGroup(Group):
    def __call__(self, *filters):
        """
        Retrieves all of the Domains the acting user has access to.

        This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           domains = client.domains()

        API Documentation: https://www.linode.com/docs/api/domains/#domains-list

        :param filters: Any number of filters to apply to this query.

        :returns: A list of Domains the acting user can access.
        :rtype: PaginatedList of Domain
        """
        return self.client._get_and_filter(Domain, *filters)

    def create(self, domain, master=True, **kwargs):
        """
        Registers a new Domain on the acting user's account.  Make sure to point
        your registrar to Linode's nameservers so that Linode's DNS manager will
        correctly serve your domain.

        API Documentation: https://www.linode.com/docs/api/domains/#domain-create

        :param domain: The domain to register to Linode's DNS manager.
        :type domain: str
        :param master: Whether this is a master (defaults to true)
        :type master: bool
        :param tags: A list of tags to apply to the new domain.  If any of the
                     tags included do not exist, they will be created as part of
                     this operation.
        :type tags: list[str]

        :returns: The new Domain object.
        :rtype: Domain
        """
        params = {
            "domain": domain,
            "type": "master" if master else "slave",
        }
        params.update(kwargs)

        result = self.client.post("/domains", data=params)

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating Domain!", json=result
            )

        d = Domain(self.client, result["id"], result)
        return d


class TagGroup(Group):
    def __call__(self, *filters):
        """
        Retrieves the Tags on your account.  This may only be attempted by
        unrestricted users.

        This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           tags = client.tags()

        API Documentation: https://www.linode.com/docs/api/domains/#domain-create

        :param filters: Any number of filters to apply to this query.

        :returns: A list of Tags on the account.
        :rtype: PaginatedList of Tag
        """
        return self.client._get_and_filter(Tag, *filters)

    def create(
        self,
        label,
        instances=None,
        domains=None,
        nodebalancers=None,
        volumes=None,
        entities=[],
    ):
        """
        Creates a new Tag and optionally applies it to the given entities.

        API Documentation: https://www.linode.com/docs/api/tags/#tags-list

        :param label: The label for the new Tag
        :type label: str
        :param entities: A list of objects to apply this Tag to upon creation.
                         May only be taggable types (Linode Instances, Domains,
                         NodeBalancers, or Volumes).  These are applied *in addition
                         to* any IDs specified with ``instances``, ``domains``,
                         ``nodebalancers``, or ``volumes``, and is a convenience
                         for sending multiple entity types without sorting them
                         yourself.
        :type entities: list of Instance, Domain, NodeBalancer, and/or Volume
        :param instances: A list of Linode Instances to apply this Tag to upon
                        creation
        :type instances: list of Instance or list of int
        :param domains: A list of Domains to apply this Tag to upon
                        creation
        :type domains: list of Domain or list of int
        :param nodebalancers: A list of NodeBalancers to apply this Tag to upon
                        creation
        :type nodebalancers: list of NodeBalancer or list of int
        :param volumes: A list of Volumes to apply this Tag to upon
                        creation
        :type volumes: list of Volumes or list of int

        :returns: The new Tag
        :rtype: Tag
        """
        linode_ids, nodebalancer_ids, domain_ids, volume_ids = [], [], [], []

        # filter input into lists of ids
        sorter = zip(
            (linode_ids, nodebalancer_ids, domain_ids, volume_ids),
            (instances, nodebalancers, domains, volumes),
        )

        for id_list, input_list in sorter:
            # if we got something, we need to find its ID
            if input_list is not None:
                for cur in input_list:
                    if isinstance(cur, int):
                        id_list.append(cur)
                    else:
                        id_list.append(cur.id)

        # filter entities into id lists too
        type_map = {
            Instance: linode_ids,
            NodeBalancer: nodebalancer_ids,
            Domain: domain_ids,
            Volume: volume_ids,
        }

        for e in entities:
            if type(e) in type_map:
                type_map[type(e)].append(e.id)
            else:
                raise ValueError("Unsupported entity type {}".format(type(e)))

        # finally, omit all id lists that are empty
        params = {
            "label": label,
            "linodes": linode_ids or None,
            "nodebalancers": nodebalancer_ids or None,
            "domains": domain_ids or None,
            "volumes": volume_ids or None,
        }

        result = self.client.post("/tags", data=params)

        if not "label" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating Tag!", json=result
            )

        t = Tag(self.client, result["label"], result)
        return t


class VolumeGroup(Group):
    def __call__(self, *filters):
        """
        Retrieves the Block Storage Volumes your user has access to.

        This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           volumes = client.volumes()

        API Documentation: https://www.linode.com/docs/api/volumes/#volumes-list

        :param filters: Any number of filters to apply to this query.

        :returns: A list of Volumes the acting user can access.
        :rtype: PaginatedList of Volume
        """
        return self.client._get_and_filter(Volume, *filters)

    def create(self, label, region=None, linode=None, size=20, **kwargs):
        """
        Creates a new Block Storage Volume, either in the given Region or
        attached to the given Instance.

        API Documentation: https://www.linode.com/docs/api/volumes/#volumes-list

        :param label: The label for the new Volume.
        :type label: str
        :param region: The Region to create this Volume in.  Not required if
                       `linode` is provided.
        :type region: Region or str
        :param linode: The Instance to attach this Volume to.  If not given, the
                       new Volume will not be attached to anything.
        :type linode: Instance or int
        :param size: The size, in GB, of the new Volume.  Defaults to 20.
        :type size: int
        :param tags: A list of tags to apply to the new volume.  If any of the
                     tags included do not exist, they will be created as part of
                     this operation.
        :type tags: list[str]

        :returns: The new Volume.
        :rtype: Volume
        """
        if not (region or linode):
            raise ValueError("region or linode required!")

        params = {
            "label": label,
            "size": size,
            "region": region.id if issubclass(type(region), Base) else region,
            "linode_id": linode.id
            if issubclass(type(linode), Base)
            else linode,
        }
        params.update(kwargs)

        result = self.client.post("/volumes", data=params)

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating volume!", json=result
            )

        v = Volume(self.client, result["id"], result)
        return v


class RegionGroup(Group):
    def __call__(self, *filters):
        """
        Returns the available Regions for Linode products.

        This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           region = client.regions()

        API Documentation: https://www.linode.com/docs/api/regions/#regions-list

        :param filters: Any number of filters to apply to the query.

        :returns: A list of available Regions.
        :rtype: PaginatedList of Region
        """

        return self.client._get_and_filter(Region, *filters)


class ImageGroup(Group):
    def __call__(self, *filters):
        """
        Retrieves a list of available Images, including public and private
        Images available to the acting user.  You can filter this query to
        retrieve only Images relevant to a specific query, for example::

           debian_images = client.images(
               Image.vendor == "debain")

        API Documentation: https://www.linode.com/docs/api/images/#images-list

        :param filters: Any number of filters to apply to the query.

        :returns: A list of available Images.
        :rtype: PaginatedList of Image
        """
        return self.client._get_and_filter(Image, *filters)

    def create(self, disk, label=None, description=None):
        """
        Creates a new Image from a disk you own.

        API Documentation: https://www.linode.com/docs/api/images/#image-create

        :param disk: The Disk to imagize.
        :type disk: Disk or int
        :param label: The label for the resulting Image (defaults to the disk's
                      label.
        :type label: str
        :param description: The description for the new Image.
        :type description: str

        :returns: The new Image.
        :rtype: Image
        """
        params = {
            "disk_id": disk.id if issubclass(type(disk), Base) else disk,
        }

        if label is not None:
            params["label"] = label

        if description is not None:
            params["description"] = description

        result = self.client.post("/images", data=params)

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating an Image from disk {}".format(
                    disk
                )
            )

        return Image(self.client, result["id"], result)

    def create_upload(
        self, label: str, region: str, description: str = None
    ) -> Tuple[Image, str]:
        """
        Creates a new Image and returns the corresponding upload URL.

        API Documentation: https://www.linode.com/docs/api/images/#image-upload

        :param label: The label of the Image to create.
        :type label: str
        :param region: The region to upload to. Once the image has been created, it can be used in any region.
        :type region: str
        :param description: The description for the new Image.
        :type description: str

        :returns: A tuple containing the new image and the image upload URL.
        :rtype: (Image, str)
        """
        params = {"label": label, "region": region, "description": description}

        result = self.client.post("/images/upload", data=drop_null_keys(params))

        if "image" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating an Image upload URL"
            )

        result_image = result["image"]
        result_url = result["upload_to"]

        return Image(self.client, result_image["id"], result_image), result_url

    def upload(
        self, label: str, region: str, file: BinaryIO, description: str = None
    ) -> Image:
        """
        Creates and uploads a new image.

        API Documentation: https://www.linode.com/docs/api/images/#image-upload

        :param label: The label of the Image to create.
        :type label: str
        :param region: The region to upload to. Once the image has been created, it can be used in any region.
        :type region: str
        :param file: The BinaryIO object to upload to the image. This is generally obtained from open("myfile", "rb").
        :param description: The description for the new Image.
        :type description: str

        :returns: The resulting image.
        :rtype: Image
        """

        image, url = self.create_upload(label, region, description=description)

        requests.put(
            url,
            headers={"Content-Type": "application/octet-stream"},
            data=file,
        )

        image._api_get()

        return image


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
    def _get_and_filter(self, obj_type, *filters):
        parsed_filters = None
        if filters:
            if len(filters) > 1:
                parsed_filters = and_(
                    *filters
                ).dct  # pylint: disable=no-value-for-parameter
            else:
                parsed_filters = filters[0].dct

        return self._get_objects(
            obj_type.api_list(), obj_type, filters=parsed_filters
        )

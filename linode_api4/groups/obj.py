from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import Base, ObjectStorageCluster, ObjectStorageKeys


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

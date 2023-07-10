from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import Base, Volume


class VolumeGroup(Group):
    def __call__(self, *filters):
        """
        Retrieves the Block Storage Volumes your user has access to.

        This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           volumes = client.volumes()

        API Documentation: https://www.linode.com/docs/api/volumes/#volumes-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

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

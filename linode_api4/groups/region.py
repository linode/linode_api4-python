from linode_api4.groups import Group
from linode_api4.objects import Region


class RegionGroup(Group):
    def __call__(self, *filters):
        """
        Returns the available Regions for Linode products.

        This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           region = client.regions()

        API Documentation: https://www.linode.com/docs/api/regions/#regions-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of available Regions.
        :rtype: PaginatedList of Region
        """

        return self.client._get_and_filter(Region, *filters)

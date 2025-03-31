from linode_api4.groups import Group
from linode_api4.objects import TieredKubeVersion


class LKETierGroup(Group):
    """
    Encapsulates methods related to a specific LKE tier. This
    should not be instantiated on its own, but should instead be used through
    an instance of :any:`LinodeClient`::

       client = LinodeClient(token)
       instances = client.lke.tier("standard") # use the LKETierGroup

    This group contains all features beneath the `/lke/tiers/{tier}` group in the API v4.
    """

    def __init__(self, client: "LinodeClient", tier: str):
        super().__init__(client)
        self.tier = tier

    def versions(self, *filters):
        """
        Returns a paginated list of versions for this tier matching the given filters.

        API Documentation: Not Yet Available

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A paginated list of kube versions that match the query.
        :rtype: PaginatedList of TieredKubeVersion
        """

        return self.client._get_and_filter(
            TieredKubeVersion,
            endpoint=f"/lke/tiers/{self.tier}/versions",
            parent_id=self.tier,
            *filters,
        )

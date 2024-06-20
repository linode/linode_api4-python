from typing import Union

from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects.placement import PlacementGroup
from linode_api4.objects.region import Region


class PlacementAPIGroup(Group):
    def groups(self, *filters):
        """
        NOTE: Placement Groups may not currently be available to all users.

        Returns a list of Placement Groups on your account.  You may filter
        this query to return only Placement Groups that match specific criteria::

           groups = client.placement.groups(PlacementGroup.label == "test")

        API Documentation: TODO

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Placement Groups that matched the query.
        :rtype: PaginatedList of PlacementGroup
        """
        return self.client._get_and_filter(PlacementGroup, *filters)

    def group_create(
        self,
        label: str,
        region: Union[Region, str],
        affinity_type: str,
        is_strict: bool = False,
        **kwargs,
    ) -> PlacementGroup:
        """
        NOTE: Placement Groups may not currently be available to all users.

        Create a placement group with the specified parameters.

        :param label: The label for the placement group.
        :type label: str
        :param region: The region where the placement group will be created. Can be either a Region object or a string representing the region ID.
        :type region: Union[Region, str]
        :param affinity_type: The affinity type of the placement group.
        :type affinity_type: PlacementGroupAffinityType
        :param is_strict: Whether the placement group is strict (defaults to False).
        :type is_strict: bool

        :returns: The new Placement Group.
        :rtype: PlacementGroup
        """
        params = {
            "label": label,
            "region": region.id if isinstance(region, Region) else region,
            "affinity_type": affinity_type,
            "is_strict": is_strict,
        }

        params.update(kwargs)

        result = self.client.post("/placement/groups", data=params)

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating Placement Group", json=result
            )

        d = PlacementGroup(self.client, result["id"], result)
        return d

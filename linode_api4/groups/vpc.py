from typing import Any, Dict, List, Optional, Union

from linode_api4 import VPCSubnet
from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import VPC, Base, Region
from linode_api4.paginated_list import PaginatedList


class VPCGroup(Group):
    def __call__(self, *filters) -> PaginatedList:
        """
        Retrieves all of the VPCs the acting user has access to.

        This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           vpcs = client.vpcs()

        API Documentation: TODO

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of VPC the acting user can access.
        :rtype: PaginatedList of VPC
        """
        return self.client._get_and_filter(VPC, *filters)

    def create(
        self,
        label: str,
        region: Union[Region, str],
        description: Optional[str] = None,
        subnets: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> VPC:
        """
        Creates a new VPC under your Linode account.

        API Documentation: TODO

        :param label: The label of the newly created VPC.
        :type label: str
        :param region: The region of the newly created VPC.
        :type region: Union[Region, str]
        :param description: The user-defined description of this VPC.
        :type description: Optional[str]
        :param subnets: A list of subnets to create under this VPC.
        :type subnets: List[Dict[str, Any]]

        :returns: The new VPC object.
        :rtype: VPC
        """
        params = {
            "label": label,
            "region": region.id if isinstance(region, Region) else region,
        }

        if description is not None:
            params["description"] = description

        if subnets is not None and len(subnets) > 0:
            for subnet in subnets:
                if not isinstance(subnet, dict):
                    raise ValueError(
                        f"Unsupported type for subnet: {type(subnet)}"
                    )

            params["subnets"] = subnets

        params.update(kwargs)

        result = self.client.post("/vpcs", data=params)

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating VPC", json=result
            )

        d = VPC(self.client, result["id"], result)
        return d

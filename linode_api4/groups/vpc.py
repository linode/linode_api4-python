from typing import Any, Dict, List, Optional, Union

from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import VPC, Region, VPCIPAddress, VPCIPv6RangeOptions
from linode_api4.objects.base import _flatten_request_body_recursive
from linode_api4.paginated_list import PaginatedList
from linode_api4.util import drop_null_keys


class VPCGroup(Group):
    def __call__(self, *filters) -> PaginatedList:
        """
        Retrieves all of the VPCs the acting user has access to.

        This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           vpcs = client.vpcs()

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-vpcs

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
        ipv6: Optional[List[Union[VPCIPv6RangeOptions, Dict[str, Any]]]] = None,
        **kwargs,
    ) -> VPC:
        """
        Creates a new VPC under your Linode account.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-vpc

        :param label: The label of the newly created VPC.
        :type label: str
        :param region: The region of the newly created VPC.
        :type region: Union[Region, str]
        :param description: The user-defined description of this VPC.
        :type description: Optional[str]
        :param subnets: A list of subnets to create under this VPC.
        :type subnets: List[Dict[str, Any]]
        :param ipv6: The IPv6 address ranges for this VPC.
        :type ipv6: List[Union[VPCIPv6RangeOptions, Dict[str, Any]]]

        :returns: The new VPC object.
        :rtype: VPC
        """
        params = {
            "label": label,
            "region": region.id if isinstance(region, Region) else region,
            "description": description,
            "ipv6": ipv6,
            "subnets": subnets,
        }

        if subnets is not None and len(subnets) > 0:
            for subnet in subnets:
                if not isinstance(subnet, dict):
                    raise ValueError(
                        f"Unsupported type for subnet: {type(subnet)}"
                    )

        params.update(kwargs)

        result = self.client.post(
            "/vpcs",
            data=drop_null_keys(_flatten_request_body_recursive(params)),
        )

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating VPC", json=result
            )

        d = VPC(self.client, result["id"], result)
        return d

    def ips(self, *filters) -> PaginatedList:
        """
        Retrieves all of the VPC IP addresses for the current account matching the given filters.

        This is intended to be called from the :any:`LinodeClient`
        class, like this::

           vpc_ips = client.vpcs.ips()

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-vpcs-ips

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of VPCIPAddresses the acting user can access.
        :rtype: PaginatedList of VPCIPAddress
        """
        return self.client._get_and_filter(
            VPCIPAddress, *filters, endpoint="/vpcs/ips"
        )

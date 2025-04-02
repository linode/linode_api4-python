from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects import Base, DerivedBase, Property, Region
from linode_api4.objects.base import _flatten_request_body_recursive
from linode_api4.objects.networking import VPCIPAddress
from linode_api4.objects.serializable import JSONObject
from linode_api4.paginated_list import PaginatedList
from linode_api4.util import drop_null_keys


@dataclass
class VPCIPv6RangeOptions(JSONObject):
    """
    VPCIPv6RangeOptions is used to specify an IPv6 range when creating or updating a VPC.
    """

    range: str = ""
    allocation_class: Optional[str] = None


@dataclass
class VPCIPv6Range(JSONObject):
    """
    VPCIPv6Range represents a single VPC IPv6 range.
    """

    put_class = VPCIPv6RangeOptions

    range: str = ""


@dataclass
class VPCSubnetIPv6RangeOptions(JSONObject):
    """
    VPCSubnetIPv6RangeOptions is used to specify an IPv6 range when creating or updating a VPC subnet.
    """

    range: str = ""


@dataclass
class VPCSubnetIPv6Range(JSONObject):
    """
    VPCSubnetIPv6Range represents a single VPC subnet IPv6 range.
    """

    put_class = VPCSubnetIPv6RangeOptions

    range: str = ""


@dataclass
class VPCSubnetLinodeInterface(JSONObject):
    id: int = 0
    active: bool = False


@dataclass
class VPCSubnetLinode(JSONObject):
    id: int = 0
    interfaces: Optional[List[VPCSubnetLinodeInterface]] = None


class VPCSubnet(DerivedBase):
    """
    An instance of a VPC subnet.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-vpc-subnet
    """

    api_endpoint = "/vpcs/{vpc_id}/subnets/{id}"
    derived_url_path = "subnets"
    parent_id_name = "vpc_id"

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True),
        "ipv4": Property(),
        "ipv6": Property(json_object=VPCSubnetIPv6Range, unordered=True),
        "linodes": Property(json_object=VPCSubnetLinode, unordered=True),
        "created": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
    }


class VPC(Base):
    """
    An instance of a VPC.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-vpc
    """

    api_endpoint = "/vpcs/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True),
        "description": Property(mutable=True),
        "region": Property(slug_relationship=Region),
        "ipv6": Property(json_object=VPCIPv6Range, unordered=True),
        "subnets": Property(derived_class=VPCSubnet),
        "created": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
    }

    def subnet_create(
        self,
        label: str,
        ipv4: Optional[str] = None,
        ipv6: Optional[
            List[Union[VPCSubnetIPv6RangeOptions, Dict[str, Any]]]
        ] = None,
        **kwargs,
    ) -> VPCSubnet:
        """
        Creates a new Subnet object under this VPC.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-vpc-subnet

        :param label: The label of this subnet.
        :type label: str
        :param ipv4: The IPv4 range of this subnet in CIDR format.
        :type ipv4: str
        :param ipv6: The IPv6 range of this subnet in CIDR format.
        :type ipv6: List[Union[VPCSubnetIPv6RangeOptions, Dict[str, Any]]]
        """
        params = {"label": label, "ipv4": ipv4, "ipv6": ipv6}

        params.update(kwargs)

        result = self._client.post(
            "{}/subnets".format(VPC.api_endpoint),
            model=self,
            data=drop_null_keys(_flatten_request_body_recursive(params)),
        )
        self.invalidate()

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response creating Subnet", json=result
            )

        d = VPCSubnet(self._client, result["id"], self.id, result)
        return d

    @property
    def ips(self) -> PaginatedList:
        """
        Get all the IP addresses under this VPC.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-vpc-ips

        :returns: A list of VPCIPAddresses the acting user can access.
        :rtype: PaginatedList of VPCIPAddress
        """

        return self._client._get_and_filter(
            VPCIPAddress, endpoint="/vpcs/{}/ips".format(self.id)
        )

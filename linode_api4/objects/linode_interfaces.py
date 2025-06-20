from dataclasses import dataclass, field
from typing import List, Optional, Union

from linode_api4.objects.base import Base, ExplicitNullValue, Property
from linode_api4.objects.dbase import DerivedBase
from linode_api4.objects.networking import Firewall
from linode_api4.objects.serializable import JSONObject


@dataclass
class LinodeInterfacesSettingsDefaultRouteOptions(JSONObject):
    """
    The options used to configure the default route settings for a Linode's network interfaces.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    ipv4_interface_id: Optional[int] = None
    ipv6_interface_id: Optional[int] = None


@dataclass
class LinodeInterfacesSettingsDefaultRoute(JSONObject):
    """
    The default route settings for a Linode's network interfaces.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    put_class = LinodeInterfacesSettingsDefaultRouteOptions

    ipv4_interface_id: Optional[int] = None
    ipv4_eligible_interface_ids: List[int] = field(default_factory=list)
    ipv6_interface_id: Optional[int] = None
    ipv6_eligible_interface_ids: List[int] = field(default_factory=list)


class LinodeInterfacesSettings(Base):
    """
    The settings related to a Linode's network interfaces.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-linode-interface-settings

    NOTE: Linode interfaces may not currently be available to all users.
    """

    api_endpoint = "/linode/instances/{id}/interfaces/settings"

    properties = {
        "id": Property(identifier=True),
        "network_helper": Property(mutable=True),
        "default_route": Property(
            mutable=True, json_object=LinodeInterfacesSettingsDefaultRoute
        ),
    }


# Interface POST Options
@dataclass
class LinodeInterfaceDefaultRouteOptions(JSONObject):
    """
    Options accepted when creating or updating a Linode Interface's default route settings.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    ipv4: Optional[bool] = None
    ipv6: Optional[bool] = None


@dataclass
class LinodeInterfaceVPCIPv4AddressOptions(JSONObject):
    """
    Options accepted for a single address when creating or updating the IPv4 configuration of a VPC Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    address: Optional[str] = None
    primary: Optional[bool] = None
    nat_1_1_address: Optional[str] = None


@dataclass
class LinodeInterfaceVPCIPv4RangeOptions(JSONObject):
    """
    Options accepted for a single range when creating or updating the IPv4 configuration of a VPC Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    range: str = ""


@dataclass
class LinodeInterfaceVPCIPv4Options(JSONObject):
    """
    Options accepted when creating or updating the IPv4 configuration of a VPC Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    addresses: Optional[List[LinodeInterfaceVPCIPv4AddressOptions]] = None
    ranges: Optional[List[LinodeInterfaceVPCIPv4RangeOptions]] = None


@dataclass
class LinodeInterfaceVPCOptions(JSONObject):
    """
    VPC-exclusive options accepted when creating or updating a Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    subnet_id: int = 0
    ipv4: Optional[LinodeInterfaceVPCIPv4Options] = None


@dataclass
class LinodeInterfacePublicIPv4AddressOptions(JSONObject):
    """
    Options accepted for a single address when creating or updating the IPv4 configuration of a public Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    address: str = ""
    primary: Optional[bool] = None


@dataclass
class LinodeInterfacePublicIPv4Options(JSONObject):
    """
    Options accepted when creating or updating the IPv4 configuration of a public Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    addresses: Optional[List[LinodeInterfacePublicIPv4AddressOptions]] = None


@dataclass
class LinodeInterfacePublicIPv6RangeOptions(JSONObject):
    """
    Options accepted for a single range when creating or updating the IPv6 configuration of a public Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    range: str = ""


@dataclass
class LinodeInterfacePublicIPv6Options(JSONObject):
    """
    Options accepted when creating or updating the IPv6 configuration of a public Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    ranges: Optional[List[LinodeInterfacePublicIPv6RangeOptions]] = None


@dataclass
class LinodeInterfacePublicOptions(JSONObject):
    """
    Public-exclusive options accepted when creating or updating a Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    ipv4: Optional[LinodeInterfacePublicIPv4Options] = None
    ipv6: Optional[LinodeInterfacePublicIPv6Options] = None


@dataclass
class LinodeInterfaceVLANOptions(JSONObject):
    """
    VLAN-exclusive options accepted when creating or updating a Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    vlan_label: str = ""
    ipam_address: Optional[str] = None


@dataclass
class LinodeInterfaceOptions(JSONObject):
    """
    Options accepted when creating or updating a Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    # If a default firewall_id isn't configured, the API requires that
    # firewall_id is defined in the LinodeInterface POST body.
    #
    # To create a Linode Interface without a firewall, this field should
    # be set to `ExplicitNullValue()`.
    firewall_id: Union[int, ExplicitNullValue, None] = None

    default_route: Optional[LinodeInterfaceDefaultRouteOptions] = None
    vpc: Optional[LinodeInterfaceVPCOptions] = None
    public: Optional[LinodeInterfacePublicOptions] = None
    vlan: Optional[LinodeInterfaceVLANOptions] = None


# Interface GET Response


@dataclass
class LinodeInterfaceDefaultRoute(JSONObject):
    """
    The default route configuration of a Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    put_class = LinodeInterfaceDefaultRouteOptions

    ipv4: bool = False
    ipv6: bool = False


@dataclass
class LinodeInterfaceVPCIPv4Address(JSONObject):
    """
    A single address under the IPv4 configuration of a VPC Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    put_class = LinodeInterfaceVPCIPv4AddressOptions

    address: str = ""
    primary: bool = False
    nat_1_1_address: Optional[str] = None


@dataclass
class LinodeInterfaceVPCIPv4Range(JSONObject):
    """
    A single range under the IPv4 configuration of a VPC Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    put_class = LinodeInterfaceVPCIPv4RangeOptions

    range: str = ""


@dataclass
class LinodeInterfaceVPCIPv4(JSONObject):
    """
    A single address under the IPv4 configuration of a VPC Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    put_class = LinodeInterfaceVPCIPv4Options

    addresses: List[LinodeInterfaceVPCIPv4Address] = field(default_factory=list)
    ranges: List[LinodeInterfaceVPCIPv4Range] = field(default_factory=list)


@dataclass
class LinodeInterfaceVPC(JSONObject):
    """
    VPC-specific configuration field for a Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    put_class = LinodeInterfaceVPCOptions

    vpc_id: int = 0
    subnet_id: int = 0

    ipv4: Optional[LinodeInterfaceVPCIPv4] = None


@dataclass
class LinodeInterfacePublicIPv4Address(JSONObject):
    """
    A single address under the IPv4 configuration of a public Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    put_class = LinodeInterfacePublicIPv4AddressOptions

    address: str = ""
    primary: bool = False


@dataclass
class LinodeInterfacePublicIPv4Shared(JSONObject):
    """
    A single shared address under the IPv4 configuration of a public Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    address: str = ""
    linode_id: int = 0


@dataclass
class LinodeInterfacePublicIPv4(JSONObject):
    """
    The IPv4 configuration of a public Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    put_class = LinodeInterfacePublicIPv4Options

    addresses: List[LinodeInterfacePublicIPv4Address] = field(
        default_factory=list
    )
    shared: List[LinodeInterfacePublicIPv4Shared] = field(default_factory=list)


@dataclass
class LinodeInterfacePublicIPv6SLAAC(JSONObject):
    """
    A single SLAAC entry under the IPv6 configuration of a public Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    address: str = ""
    prefix: int = 0


@dataclass
class LinodeInterfacePublicIPv6Shared(JSONObject):
    """
    A single shared range under the IPv6 configuration of a public Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    range: str = ""
    route_target: Optional[str] = None


@dataclass
class LinodeInterfacePublicIPv6Range(JSONObject):
    """
    A single range under the IPv6 configuration of a public Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    put_class = LinodeInterfacePublicIPv6RangeOptions

    range: str = ""
    route_target: Optional[str] = None


@dataclass
class LinodeInterfacePublicIPv6(JSONObject):
    """
    The IPv6 configuration of a Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    put_class = LinodeInterfacePublicIPv6Options

    slaac: List[LinodeInterfacePublicIPv6SLAAC] = field(default_factory=list)
    shared: List[LinodeInterfacePublicIPv6Shared] = field(default_factory=list)
    ranges: List[LinodeInterfacePublicIPv6Range] = field(default_factory=list)


@dataclass
class LinodeInterfacePublic(JSONObject):
    """
    Public-specific configuration fields for a Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    put_class = LinodeInterfacePublicOptions

    ipv4: Optional[LinodeInterfacePublicIPv4] = None
    ipv6: Optional[LinodeInterfacePublicIPv6] = None


@dataclass
class LinodeInterfaceVLAN(JSONObject):
    """
    VLAN-specific configuration fields for a Linode Interface.

    NOTE: Linode interfaces may not currently be available to all users.
    """

    put_class = LinodeInterfaceVLANOptions

    vlan_label: str = ""
    ipam_address: Optional[str] = None


class LinodeInterface(DerivedBase):
    """
    A Linode's network interface.

    NOTE: Linode interfaces may not currently be available to all users.

    NOTE: When using the ``save()`` method, certain local fields with computed values will
          not be refreshed on the local object until after ``invalidate()`` has been called::

            # Automatically assign an IPv4 address from the associated VPC Subnet
            interface.vpc.ipv4.addresses[0].address = "auto"

            # Save the interface
            interface.save()

            # Invalidate the interface
            interface.invalidate()

            # Access the new address
            print(interface.vpc.ipv4.addresses[0].address)

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-linode-interface
    """

    api_endpoint = "/linode/instances/{linode_id}/interfaces/{id}"
    derived_url_path = "interfaces"
    parent_id_name = "linode_id"

    properties = {
        "linode_id": Property(identifier=True),
        "id": Property(identifier=True),
        "mac_address": Property(),
        "created": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
        "version": Property(),
        "default_route": Property(
            mutable=True,
            json_object=LinodeInterfaceDefaultRoute,
        ),
        "public": Property(mutable=True, json_object=LinodeInterfacePublic),
        "vlan": Property(mutable=True, json_object=LinodeInterfaceVLAN),
        "vpc": Property(mutable=True, json_object=LinodeInterfaceVPC),
    }

    def firewalls(self, *filters) -> List[Firewall]:
        """
        Retrieves a list of Firewalls for this Linode Interface.
        Linode interfaces are not interchangeable with Config interfaces.

        NOTE: Linode interfaces may not currently be available to all users.

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A List of Firewalls for this Linode Interface.
        :rtype: List[Firewall]

        NOTE: Caching is disabled on this method and each call will make
        an additional Linode API request.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-linode-interface-firewalls
        """

        return self._client._get_and_filter(
            Firewall,
            *filters,
            endpoint="{}/firewalls".format(LinodeInterface.api_endpoint).format(
                **vars(self)
            ),
        )

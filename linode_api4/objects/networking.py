from dataclasses import dataclass, field
from typing import List, Optional

from linode_api4.common import Price, RegionPrice
from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects.base import Base, Property
from linode_api4.objects.dbase import DerivedBase
from linode_api4.objects.region import Region
from linode_api4.objects.serializable import JSONObject
from linode_api4.paginated_list import PaginatedList


class IPv6Pool(Base):
    """
    DEPRECATED
    """

    api_endpoint = "/networking/ipv6/pools/{range}"
    id_attribute = "range"

    properties = {
        "range": Property(identifier=True),
        "region": Property(slug_relationship=Region),
    }


class IPv6Range(Base):
    """
    An instance of a Linode IPv6 Range.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-ipv6-range
    """

    api_endpoint = "/networking/ipv6/ranges/{range}"
    id_attribute = "range"

    properties = {
        "range": Property(identifier=True),
        "region": Property(slug_relationship=Region),
        "prefix": Property(),
        "route_target": Property(),
        "linodes": Property(
            unordered=True,
        ),
        "is_bgp": Property(),
    }


@dataclass
class InstanceIPNAT1To1(JSONObject):
    """
    InstanceIPNAT1To1 contains information about the NAT 1:1 mapping
    of VPC IP together with the VPC and subnet ids.
    """

    address: str = ""
    subnet_id: int = 0
    vpc_id: int = 0


@dataclass
class ReservedIPAssignedEntity(JSONObject):
    """
    Represents the entity that a reserved IP is assigned to.

    NOTE: Reserved IP feature may not currently be available to all users.
    """

    id: int = 0
    label: str = ""
    type: str = ""
    url: str = ""


class IPAddress(Base):
    """
    note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.

    Represents a Linode IP address object.

    When attempting to reset the `rdns` field to default, consider using the ExplicitNullValue class::

        ip = IPAddress(client, "127.0.0.1")
        ip.rdns = ExplicitNullValue
        ip.save()

        # Re-populate all attributes with new information from the API
        ip.invalidate()

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-ip
    """

    api_endpoint = "/networking/ips/{address}"
    id_attribute = "address"

    properties = {
        "address": Property(identifier=True),
        "gateway": Property(),
        "subnet_mask": Property(),
        "prefix": Property(),
        "type": Property(),
        "public": Property(),
        "rdns": Property(mutable=True),
        "linode_id": Property(),
        "interface_id": Property(),
        "region": Property(slug_relationship=Region),
        "vpc_nat_1_1": Property(json_object=InstanceIPNAT1To1),
        "reserved": Property(mutable=True),
        "tags": Property(mutable=True, unordered=True),
        "assigned_entity": Property(json_object=ReservedIPAssignedEntity),
    }

    @property
    def linode(self):
        from .linode import Instance  # pylint: disable-all

        if not hasattr(self, "_linode"):
            self._set("_linode", Instance(self._client, self.linode_id))

        return self._linode

    @property
    def interface(self) -> Optional["LinodeInterface"]:
        """
        Returns the Linode Interface associated with this IP address.

        NOTE: This function will only return Linode interfaces, not Config interfaces.

        :returns: The Linode Interface associated with this IP address.
        :rtype: LinodeInterface
        """

        from .linode_interfaces import LinodeInterface  # pylint: disable-all

        if self.interface_id in (None, 0):
            self._set("_interface", None)
        elif not hasattr(self, "_interface"):
            self._set(
                "_interface",
                LinodeInterface(
                    self._client, self.linode_id, self.interface_id
                ),
            )

        return self._interface

    def to(self, linode):
        """
        This is a helper method for ip-assign, and should not be used outside
        of that context.  It's used to cleanly build an IP Assign request with
        pretty python syntax.
        """
        from .linode import Instance  # pylint: disable-all

        if not isinstance(linode, Instance):
            raise ValueError("IP Address can only be assigned to a Linode!")

        return {"address": self.address, "linode_id": linode.id}

    def delete(self):
        """
        Override the delete() function from Base to use the correct endpoint.
        """
        resp = self._client.delete(
            "/linode/instances/{}/ips/{}".format(self.linode_id, self.address),
            model=self,
        )

        if "error" in resp:
            return False
        self.invalidate()
        return True


class ReservedIPAddress(Base):
    """
    .. note:: This endpoint is in beta. This will only function if base_url is set to ``https://api.linode.com/v4beta``.

    Represents a Linode Reserved IPv4 Address.

    Update tags on a reserved IP by mutating the ``tags`` attribute and calling ``save()``.

    NOTE: Reserved IP feature may not currently be available to all users.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-reserved-ip
    """

    api_endpoint = "/networking/reserved/ips/{address}"
    id_attribute = "address"

    properties = {
        "address": Property(identifier=True),
        "gateway": Property(),
        "linode_id": Property(),
        "prefix": Property(),
        "public": Property(),
        "rdns": Property(),
        "region": Property(slug_relationship=Region),
        "reserved": Property(),
        "subnet_mask": Property(),
        "tags": Property(mutable=True, unordered=True),
        "type": Property(),
        "assigned_entity": Property(json_object=ReservedIPAssignedEntity),
        "interface_id": Property(),
        "vpc_nat_1_1": Property(json_object=InstanceIPNAT1To1),
    }


@dataclass
class VPCIPAddressIPv6(JSONObject):
    slaac_address: str = ""


@dataclass
class VPCIPAddressNATGatewayPortsetPort(JSONObject):
    start: int = 0
    end: int = 0


@dataclass
class VPCIPAddressNATGatewayPortset(JSONObject):
    address: str = ""
    ports: List[VPCIPAddressNATGatewayPortsetPort] = field(default_factory=list)


@dataclass
class VPCIPAddressNATGateway(JSONObject):
    """
    A NAT gateway under a VPC IP Address.
    """

    id: int = 0
    addresses: List[str] = field(default_factory=list)
    portset_assignments: int = 0
    portset_capacity: int = 0
    portsets: List[VPCIPAddressNATGatewayPortset] = field(
        default_factory=list
    )  # NOTE: This field may not be available to all users.


@dataclass
class VPCIPAddress(JSONObject):
    """
    VPCIPAddress represents the IP address of a VPC.

    NOTE: This is not implemented as a typical API object (Base) because VPC IPs
    cannot be refreshed through the /networking/ips/{address} endpoint.
    """

    address: str = ""
    gateway: str = ""
    region: str = ""
    subnet_mask: str = ""
    vpc_id: int = 0
    subnet_id: int = 0
    linode_id: int = 0
    config_id: int = 0
    interface_id: int = 0
    prefix: int = 0

    active: bool = False

    address_range: Optional[str] = None
    nat_1_1: Optional[str] = None

    ipv6_range: Optional[str] = None
    ipv6_is_public: Optional[bool] = None
    ipv6_addresses: Optional[List[VPCIPAddressIPv6]] = None
    natgateway: Optional[VPCIPAddressNATGateway] = None


class VLAN(Base):
    """
    .. note:: At this time, the Linode API only supports listing VLANs.
    .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.

    An instance of a Linode VLAN.
    VLANs provide a mechanism for secure communication between two or more Linodes that are assigned to the same VLAN.
    VLANs are implicitly created during Instance or Instance Config creation.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-vlans
    """

    api_endpoint = "/networking/vlans/{label}"
    id_attribute = "label"

    properties = {
        "label": Property(identifier=True),
        "created": Property(is_datetime=True),
        "linodes": Property(unordered=True),
        "region": Property(slug_relationship=Region),
    }


@dataclass
class FirewallCreateDevicesOptions(JSONObject):
    """
    Represents devices to create created alongside a Linode Firewall.
    """

    linodes: List[int] = field(default_factory=list)
    nodebalancers: List[int] = field(default_factory=list)
    linode_interfaces: List[int] = field(default_factory=list)


@dataclass
class FirewallSettingsDefaultFirewallIDs(JSONObject):
    """
    Contains the IDs of Linode Firewalls that should be used by default
    when creating various interface types.

    NOTE: This feature may not currently be available to all users.
    """

    include_none_values = True

    vpc_interface: Optional[int] = None
    public_interface: Optional[int] = None
    linode: Optional[int] = None
    nodebalancer: Optional[int] = None


class FirewallSettings(Base):
    """
    Represents the Firewall settings for the current user.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-firewall-settings

    NOTE: This feature may not currently be available to all users.
    """

    api_endpoint = "/networking/firewalls/settings"

    properties = {
        "default_firewall_ids": Property(
            json_object=FirewallSettingsDefaultFirewallIDs,
            mutable=True,
        ),
    }


class FirewallDevice(DerivedBase):
    """
    An object representing the assignment between a Linode Firewall and another Linode resource.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-firewall-device
    """

    api_endpoint = "/networking/firewalls/{firewall_id}/devices/{id}"
    derived_url_path = "devices"
    parent_id_name = "firewall_id"

    properties = {
        "created": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
        "entity": Property(),
        "id": Property(identifier=True),
    }


class Firewall(Base):
    """
    .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.

    An instance of a Linode Cloud Firewall.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-firewall
    """

    api_endpoint = "/networking/firewalls/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True),
        "tags": Property(mutable=True, unordered=True),
        "status": Property(mutable=True),
        "created": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
        "devices": Property(derived_class=FirewallDevice),
        "rules": Property(),
    }

    def update_rules(self, rules):
        """
        Sets the JSON rules for this Firewall.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/put-firewall-rules

        :param rules: The rules to apply to this Firewall.
        :type rules: dict
        """
        self._client.put(
            "{}/rules".format(self.api_endpoint), model=self, data=rules
        )
        self.invalidate()

    def get_rules(self):
        """
        Gets the JSON rules for this Firewall.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/put-firewall-rules

        :returns: The rules that this Firewall is currently configured with.
        :rtype: dict
        """
        return self._client.get(
            "{}/rules".format(self.api_endpoint), model=self
        )

    @property
    def rule_versions(self):
        """
        Gets the JSON rule versions for this Firewall.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-firewall-rule-versions

        :returns: Lists the current and historical rules of the firewall (that is not deleted),
                using version. Whenever the rules update, the version increments from 1.
        :rtype: dict
        """
        return self._client.get(
            "{}/history".format(self.api_endpoint), model=self
        )

    def get_rule_version(self, version):
        """
        Gets the JSON for a specific rule version for this Firewall.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-firewall-rule-version

        :param version: The firewall rule version to view.
        :type version: int

        :returns: Gets a specific firewall rule version for an enabled or disabled firewall.
        :rtype: dict
        """
        return self._client.get(
            "{}/history/rules/{}".format(self.api_endpoint, version), model=self
        )

    def device_create(self, id, type="linode", **kwargs):
        """
        Creates and attaches a device to this Firewall

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-firewall-device

        :param id: The ID of the entity to create a device for.
        :type id: int

        :param type: The type of entity the device is being created for. (`linode`)
        :type type: str
        """
        params = {
            "id": id,
            "type": type,
        }
        params.update(kwargs)

        result = self._client.post(
            "{}/devices".format(Firewall.api_endpoint), model=self, data=params
        )
        self.invalidate()

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response creating device!", json=result
            )

        c = FirewallDevice(self._client, result["id"], self.id, result)
        return c


class FirewallTemplate(Base):
    """
    Represents a single Linode Firewall template.

    API documentation: https://techdocs.akamai.com/linode-api/reference/get-firewall-template

    NOTE: This feature may not currently be available to all users.
    """

    api_endpoint = "/networking/firewalls/templates/{slug}"

    id_attribute = "slug"

    properties = {"slug": Property(identifier=True), "rules": Property()}


class NetworkTransferPrice(Base):
    """
    An NetworkTransferPrice represents the structure of a valid network transfer price.
    Currently the NetworkTransferPrice can only be retrieved by listing, i.e.:
        types = client.networking.transfer_prices()

    API documentation: https://techdocs.akamai.com/linode-api/reference/get-network-transfer-prices
    """

    properties = {
        "id": Property(identifier=True),
        "label": Property(),
        "price": Property(json_object=Price),
        "region_prices": Property(json_object=RegionPrice),
        "transfer": Property(),
    }


class ReservedIPType(Base):
    """
    Represents a reserved IP type with pricing information.

    NOTE: Reserved IP feature may not currently be available to all users.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-reserved-ip-types
    """

    properties = {
        "id": Property(identifier=True),
        "label": Property(),
        "price": Property(json_object=Price),
        "region_prices": Property(json_object=RegionPrice),
    }


@dataclass
class NATGatewayAddress(JSONObject):
    address: str = ""


@dataclass
class NATGatewayVPCSubnet(JSONObject):
    id: int = 0
    type: str = ""
    label: str = ""
    url: str = ""
    vpc_id: int = 0
    vpc_label: str = ""


@dataclass
class NATGatewayAddressAssignment(JSONObject):
    address: str = ""
    in_use: bool = False
    interface_count: int = 0
    interface_url: str = ""
    portset_assignments: int = 0
    portset_capacity: int = 0


@dataclass
class NATGatewayInterfaceLinode(JSONObject):
    id: int = 0
    label: str = ""
    type: str = ""
    url: str = ""


@dataclass
class NATGatewayInterfacePortsetPort(JSONObject):
    start: int = 0
    end: int = 0


@dataclass
class NATGatewayInterfacePortset(JSONObject):
    address: str = ""
    ports: List[NATGatewayInterfacePortsetPort] = field(default_factory=list)


@dataclass
class NATGatewayInterface(JSONObject):
    id: int = 0
    linode: Optional[NATGatewayInterfaceLinode] = None
    addresses: List[str] = field(default_factory=list)
    portsets: List[NATGatewayInterfacePortset] = field(
        default_factory=list
    )  # NOTE: This field may not be available to all users.


@dataclass
class NATGatewayType(JSONObject):
    id: str = ""
    label: str = ""
    price: Optional[Price] = None


@dataclass
class NATGatewaySettings(JSONObject):
    allowed_ports_per_interface: List[int] = field(default_factory=list)
    maximum_autoscaling_addresses_per_natgateway: int = 0
    maximum_reserved_addresses_per_natgateway: int = 0


class NATGateway(Base):
    """
    Represents a single Linode NAT Gateway.

    API documentation: TODO

    NOTE: This feature may not currently be available to all users.
    """

    api_endpoint = "/networking/natgateways/{id}"

    id_attribute = "id"

    properties = {
        "id": Property(identifier=True),
        "region": Property(),
        "addresses": Property(json_object=NATGatewayAddress),
        "address_autoscale_max": Property(),
        "default_ports_per_interface": Property(),
        "label": Property(mutable=True),
        "portset_assignments": Property(),
        "portset_capacity": Property(),
        "vpc_subnet": Property(json_object=NATGatewayVPCSubnet),
        "created": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
    }

    def address_assignments(self, *filters) -> PaginatedList:
        """
        Retrieves the reserved IP address assignments for this NAT Gateway.

        API Documentation: TODO

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A paginated list of address assignments for this NAT Gateway.
        :rtype: PaginatedList of NATGatewayAddressAssignment
        """
        return self._client._get_and_filter(
            NATGatewayAddressAssignment,
            *filters,
            endpoint="{}/addresses".format(NATGateway.api_endpoint).format(
                id=self.id
            ),
        )

    def address_assignment_view(
        self, address: str
    ) -> NATGatewayAddressAssignment:
        """
        Retrieves a single reserved IP address assignment for this NAT Gateway.

        API Documentation: TODO

        :param address: The reserved IPv4 address to look up.
        :type address: str

        :returns: The requested address assignment.
        :rtype: NATGatewayAddressAssignment
        """
        result = self._client.get(
            "{}/addresses/{}".format(NATGateway.api_endpoint, address),
            model=self,
        )
        return NATGatewayAddressAssignment.from_json(result)

    def address_assignment_create(
        self, address: str
    ) -> NATGatewayAddressAssignment:
        """
        Assigns a reserved IP address to this NAT Gateway.

        API Documentation: TODO

        :param address: The reserved IPv4 address to assign to this NAT Gateway.
        :type address: str

        :returns: The new address assignment.
        :rtype: NATGatewayAddressAssignment
        """
        result = self._client.post(
            "{}/addresses".format(NATGateway.api_endpoint),
            model=self,
            data={"address": address},
        )

        if "address" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when assigning address to NAT Gateway!",
                json=result,
            )

        return NATGatewayAddressAssignment.from_json(result)

    def address_assignment_delete(self, address: str) -> bool:
        """
        Removes a reserved IP address assignment from this NAT Gateway.

        API Documentation: TODO

        :param address: The reserved IPv4 address to remove from this NAT Gateway.
        :type address: str

        :returns: True if the delete request succeeded.
        :rtype: bool
        """
        resp = self._client.delete(
            "{}/addresses/{}".format(NATGateway.api_endpoint, address),
            model=self,
        )

        if "error" in resp:
            return False
        return True

    def interfaces(self, *filters) -> PaginatedList:
        """
        Retrieves the Linode Interfaces attached to this NAT Gateway.

        API Documentation: TODO

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A paginated list of interfaces attached to this NAT Gateway.
        :rtype: PaginatedList of NATGatewayInterface
        """
        return self._client._get_and_filter(
            NATGatewayInterface,
            *filters,
            endpoint="{}/interfaces".format(NATGateway.api_endpoint).format(
                id=self.id
            ),
        )

    def address_interfaces(self, address: str, *filters) -> PaginatedList:
        """
        Retrieves the Linode Interfaces using the given reserved IP address on this NAT Gateway.

        API Documentation: TODO

        :param address: The reserved IPv4 address to look up interfaces for.
        :type address: str
        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A paginated list of interfaces using the given address.
        :rtype: PaginatedList of NATGatewayInterface
        """
        return self._client._get_and_filter(
            NATGatewayInterface,
            *filters,
            endpoint="{}/addresses/{}/interfaces".format(
                NATGateway.api_endpoint, address
            ).format(id=self.id),
        )

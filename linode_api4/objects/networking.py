from dataclasses import dataclass
from typing import Optional

from linode_api4.common import Price, RegionPrice
from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects.base import Base, Property
from linode_api4.objects.dbase import DerivedBase
from linode_api4.objects.region import Region
from linode_api4.objects.serializable import JSONObject


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
        "region": Property(slug_relationship=Region),
        "vpc_nat_1_1": Property(json_object=InstanceIPNAT1To1),
    }

    @property
    def linode(self):
        from .linode import Instance  # pylint: disable-all

        if not hasattr(self, "_linode"):
            self._set("_linode", Instance(self._client, self.linode_id))
        return self._linode

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

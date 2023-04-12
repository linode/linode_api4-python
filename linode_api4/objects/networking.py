from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects import Base, DerivedBase, Property, Region


class IPv6Pool(Base):
    api_endpoint = "/networking/ipv6/pools/{}"
    id_attribute = "range"

    properties = {
        "range": Property(identifier=True),
        "region": Property(slug_relationship=Region, filterable=True),
        "prefix": Property(),
        "route_target": Property(),
    }

    def _api_get(self):
        """
        A helper method to GET this object from the server
        """
        pools = self._client.networking.ipv6_pools()
        pool = [p for p in pools if p.range == self.range][0]

        if pool is not None:
            self._populate(pool._raw_json)
        else:
            raise LookupError("Could not find IPv6 pool with proviced range.")


class IPv6Range(Base):
    api_endpoint = "/networking/ipv6/ranges/{range}"
    id_attribute = "range"

    properties = {
        "range": Property(identifier=True),
        "region": Property(slug_relationship=Region, filterable=True),
        "prefix": Property(),
        "route_target": Property(),
    }

    def ip_ranges_list(self):
        """
        Displays the IPv6 ranges on your Account.
        """

        result = self._client.post("/networking/ipv6/ranges", model=self)

        return [IPv6Range(self._client, r["range"]) for r in result["data"]]

    def ip_range_delete(self):
        """
        Removes this IPv6 range from your account and disconnects the range from any assigned Linodes.
        """

        self._client.delete("{}".format(self.api_endpoint), model=self)


class IPAddress(Base):
    """
    note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.
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
        "region": Property(slug_relationship=Region, filterable=True),
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

    def ip_addresses_share(self, ips, linode_id):
        """
        Configure shared IPs.
        """

        params = {
            "ips": ips if not isinstance(ips[0], IPAddress) else [ip.address for ip in ips],
            "linode_id": linode_id,
        }

        self._client.post("/networking/ips/share", model=self, data=params)

    def ip_addresses_assign(self, assignments, region):
        """
        Assign multiple IPv4 addresses and/or IPv6 ranges to multiple Linodes in one Region.
        """

        for a in assignments:
            if not "address" in a or not "linode_id" in a:
                raise ValueError("Invalid assignment: {}".format(a))

        if isinstance(region, Region):
            region = region.id

        params = {"assignments": assignments, "region": region}

        self._client.post("/networking/ips/assign", model=self, data=params)


class VLAN(Base):
    """
    .. note:: At this time, the Linode API only supports listing VLANs.
    .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.
    """

    api_endpoint = "/networking/vlans/{}"
    id_attribute = "label"

    properties = {
        "label": Property(identifier=True),
        "created": Property(is_datetime=True),
        "linodes": Property(filterable=True),
        "region": Property(slug_relationship=Region, filterable=True),
    }


class FirewallDevice(DerivedBase):
    api_endpoint = "/networking/firewalls/{firewall_id}/devices/{id}"
    derived_url_path = "devices"
    parent_id_name = "firewall_id"

    properties = {
        "created": Property(filterable=True, is_datetime=True),
        "updated": Property(filterable=True, is_datetime=True),
        "entity": Property(),
        "id": Property(identifier=True),
    }


class Firewall(Base):
    """
    .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.
    """

    api_endpoint = "/networking/firewalls/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True, filterable=True),
        "tags": Property(mutable=True, filterable=True),
        "status": Property(mutable=True),
        "created": Property(filterable=True, is_datetime=True),
        "updated": Property(filterable=True, is_datetime=True),
        "devices": Property(derived_class=FirewallDevice),
        "rules": Property(),
    }

    def update_rules(self, rules):
        """
        Sets the JSON rules for this Firewall
        """
        self._client.put(
            "{}/rules".format(self.api_endpoint), model=self, data=rules
        )
        self.invalidate()

    def get_rules(self):
        """
        Gets the JSON rules for this Firewall
        """
        return self._client.get(
            "{}/rules".format(self.api_endpoint), model=self
        )

    def device_create(self, id, type="linode", **kwargs):
        """
        Creates and attaches a device to this Firewall

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

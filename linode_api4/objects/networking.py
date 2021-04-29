from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects import Base, DerivedBase, Property, Region


class IPv6Pool(Base):
    api_endpoint = '/networking/ipv6/pools/{}'
    id_attribute = 'range'

    properties = {
        'range': Property(identifier=True),
        'region': Property(slug_relationship=Region, filterable=True),
    }


class IPv6Range(Base):
    api_endpoint = '/networking/ipv6/ranges/{}'
    id_attribute = 'range'

    properties = {
        'range': Property(identifier=True),
        'region': Property(slug_relationship=Region, filterable=True),
    }


class IPAddress(Base):
    api_endpoint = '/networking/ips/{address}'
    id_attribute = 'address'

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
        from .linode import Instance # pylint: disable-all
        if not hasattr(self, '_linode'):
            self._set('_linode', Instance(self._client, self.linode_id))
        return self._linode

    def to(self, linode):
        """
        This is a helper method for ip-assign, and should not be used outside
        of that context.  It's used to cleanly build an IP Assign request with
        pretty python syntax.
        """
        from .linode import Instance # pylint: disable-all
        if not isinstance(linode, Instance):
            raise ValueError("IP Address can only be assigned to a Linode!")
        return { "address": self.address, "linode_id": linode.id }



class VLAN(Base):
    """
    .. note:: At this time, the Linode API only supports listing VLANs.
    .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.
    """
    api_endpoint = '/networking/vlans/{}'
    id_attribute = 'label'

    properties = {
        'label': Property(identifier=True),
        'created': Property(is_datetime=True),
        'linodes': Property(filterable=True),
        'region': Property(slug_relationship=Region, filterable=True)
    }


class FirewallDevice(DerivedBase):
    api_endpoint = '/networking/firewalls/{firewall_id}/devices/{id}'
    derived_url_path = 'devices'
    parent_id_name = 'firewall_id'

    properties = {
        'created': Property(filterable=True, is_datetime=True),
        'updated': Property(filterable=True, is_datetime=True),
        'entity': Property(),
        'id': Property(identifier=True)
    }


class Firewall(Base):
    """
    .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.
    """

    api_endpoint = "/networking/firewalls/{id}"

    properties = {
        'id': Property(identifier=True),
        'label': Property(mutable=True, filterable=True),
        'tags': Property(mutable=True, filterable=True),
        'status': Property(mutable=True),
        'created': Property(filterable=True, is_datetime=True),
        'updated': Property(filterable=True, is_datetime=True),
        'devices': Property(derived_class=FirewallDevice),
        'rules': Property(),
    }
    def update_rules(self, rules):
        """
        Sets the JSON rules for this Firewall
        """
        self._client.put('{}/rules'.format(self.api_endpoint), model=self, data=rules)
        self.invalidate()

    def device_create(self, id, type='linode', **kwargs):
        """
        Creates and attaches a device to this Firewall

        :param id: The ID of the entity to create a device for.
        :type id: int

        :param type: The type of entity the device is being created for. (`linode`)
        :type type: str
        """
        params = {
            'id': id,
            'type': type,
        }
        params.update(kwargs)

        result = self._client.post("{}/devices".format(Firewall.api_endpoint), model=self, data=params)
        self.invalidate()

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response creating device!', json=result)

        c = FirewallDevice(self._client, result['id'], self.id, result)
        return c

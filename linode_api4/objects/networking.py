from linode_api4.objects import Base, Property, Region


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

from __future__ import absolute_import

from linode.objects import Base, Property, Region


class IPAddress(Base):
    api_endpoint = '/networking/ips/{address}'
    id_attribute = 'address'

    properties = {
        "address": Property(identifier=True),
        "gateway": Property(),
        "subnet_mask": Property(),
        "prefix": Property(),
        "type": Property(),
        "rdns": Property(mutable=True),
        "linode_id": Property(),
        "region": Property(slug_relationship=Region, filterable=True),
    }

    @property
    def linode(self):
        from ..linode import Linode
        if not hasattr(self, '_linode'):
            self._set('_linode', Linode(self._client, self.linode_id))
        return self._linode

    def to(self, linode):
        """
        This is a helper method for ip-assign, and should not be used outside
        of that context.  It's used to cleanly build an IP Assign request with
        pretty python syntax.
        """
        from ..linode import Linode
        if not isinstance(linode, Linode):
            raise ValueError("IP Address can only be assigned to a Linode!")
        return { "address": self.address, "linode_id": linode.id }

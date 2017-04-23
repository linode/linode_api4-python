from .. import Base, Property
from ..region import Region

class IPAddress(Base):
    api_name = 'ipv4s'
    api_endpoint = '/networking/ipv4/{address}'
    id_attribute = 'address'

    properties = {
        "address": Property(identifier=True),
        "gateway": Property(),
        "subnet_mask": Property(),
        "prefix": Property(),
        "type": Property(),
        "rdns": Property(mutable=True),
        "linode_id": Property(),
        "region": Property(relationship=Region, filterable=True),
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

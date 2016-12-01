from .. import Base, Property

class IPAddress(Base):
    api_name = 'ipv4s'
    api_endpoint = '/networking/ipv4/{address}'
    id_attribute = 'address'

    properties = {
        'linode_id': Property(),
        'address': Property(),
        'rdns': Property(mutable=True),
    }

    @property
    def linode(self):
        from ..linode import Linode
        if not hasattr(self, '_linode'):
            self._set('_linode', Linode(self._client, self.linode_id))
        return self._linode

    def to(self, linode):
        from ..linode import Linode
        if not isinstance(linode, Linode):
            raise ValueError("IP Address can only be assigned to a Linode!")
        return { "address": self.address, "linode_id": linode.id }

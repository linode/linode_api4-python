from .. import Base, Property

class IPAddress(Base):
    api_name = 'ipv4s'
    api_endpoint = '/networking/ipv4/{address}'
    id_attribute = 'address'

    properties = {
        'linode_id': Property(identifier=True),
        'address': Property(),
        'rdns': Property(mutable=True),
    }

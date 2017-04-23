from .. import Base, Property

class IPv6Pool(Base):
    api_name = 'ipv6_pools'
    api_endpoint = '/networking/ipv6/{}'
    id_attribute = 'range'

    properties = {
        'range': Property(identifier=True),
        'region': Property(filterable=True),
    }

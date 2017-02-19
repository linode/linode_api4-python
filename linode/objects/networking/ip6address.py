from .. import Base, Property

class IPv6Address(Base):
    api_name = 'ipv6'
    api_endpoint = 'networking/ipv6/{address}'
    id_attribute = 'address'

    properties = {
        "address": Property(identifier=True),
        "gateway": Property(),
        "range": Property(),
        "rdns": Property(mutable=True),
        "prefix": Property(),
        "subnet_mask": Property(),
        "type": Property(),
    }

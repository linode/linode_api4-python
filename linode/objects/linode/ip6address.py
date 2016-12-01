from .. import Base, Property

class IPv6Address(Base):
    api_name = 'ipv6'
    api_endpoint = 'networking/ipv6/{address}'

    properties = {
        'address': Property(),
        'rdns': Property(mutable=True),
    }

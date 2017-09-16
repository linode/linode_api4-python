from .. import Base, Property
from ..region import Region

class IPv6Address(Base):
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
        "region": Property(slug_relationship=Region),
    }

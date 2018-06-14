from __future__ import absolute_import

from linode_api.objects import Base, Property, Region


class IPv6Pool(Base):
    api_endpoint = '/networking/ipv6/pools/{}'
    id_attribute = 'range'

    properties = {
        'range': Property(identifier=True),
        'region': Property(slug_relationship=Region, filterable=True),
    }

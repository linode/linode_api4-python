from __future__ import absolute_import

from linode.objects import Base, Property, Region


class IPv6Pool(Base):
    api_endpoint = '/networking/ipv6/{}'
    id_attribute = 'range'

    properties = {
        'range': Property(identifier=True),
        'region': Property(slug_relationship=Region, filterable=True),
    }

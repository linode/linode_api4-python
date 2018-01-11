from __future__ import absolute_import

from linode.objects import Base, Property


class Type(Base):
    api_endpoint = "/linode/types/{id}"
    properties = {
        'disk': Property(filterable=True),
        'id': Property(identifier=True),
        'label': Property(filterable=True),
        'network_out': Property(filterable=True),
        'price': Property(),
        'addons': Property(),
        'memory': Property(filterable=True),
        'transfer': Property(filterable=True),
        'vcpus': Property(filterable=True),
    }

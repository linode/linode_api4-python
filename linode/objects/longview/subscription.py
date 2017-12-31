from __future__ import absolute_import

from linode.objects import Base, Property


class LongviewSubscription(Base):
    api_endpoint = 'longview/subscriptions/{id}'
    properties = {
        "id": Property(identifier=True),
        "label": Property(),
        "clients_included": Property(),
        "price": Property()
    }

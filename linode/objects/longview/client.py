from __future__ import absolute_import

from linode.objects import Base, Property


class LongviewClient(Base):

    api_endpoint = '/longview/clients/{id}'

    properties= {
        "id": Property(identifier=True),
        "created": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
        "label": Property(mutable=True, filterable=True),
        "install_code": Property(),
        "apps": Property(),
        "api_key": Property(),
    }

from __future__ import absolute_import

from linode.objects import Base, Property


class Invoice(Base):
    api_endpoint = "/account/invoices/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(),
        "date": Property(is_datetime=True),
        "total": Property(),
    }

from __future__ import absolute_import

from linode.objects import Base, Property


class Payment(Base):
    api_endpoint = "/account/payments/{id}"

    properties = {
        "id": Property(identifier=True),
        "date": Property(is_datetime=True),
        "amount": Property(),
    }

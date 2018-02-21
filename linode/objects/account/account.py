from __future__ import absolute_import

from linode.objects import Base, Property


class Account(Base):
    api_endpoint = "/account"
    id_attribute = 'email'

    properties = {
        "company": Property(mutable=True),
        "country": Property(mutable=True),
        "balance": Property(),
        "address_1": Property(mutable=True),
        "last_name": Property(mutable=True),
        "city": Property(mutable=True),
        "state": Property(mutable=True),
        "first_name": Property(mutable=True),
        "phone": Property(mutable=True),
        "email": Property(mutable=True),
        "zip": Property(mutable=True),
        "address_2": Property(mutable=True),
        "tax_id": Property(mutable=True),
    }

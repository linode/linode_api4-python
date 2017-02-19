from linode.objects import Base, Property

class AccountSettings(Base):
    api_name = 'settings' # should never come up
    api_endpoint = "/account/settings"
    id_attribute = 'email'

    properties = {
        "company": Property(mutable=True),
        "country": Property(mutable=True),
        "balance": Property(),
        "address_1": Property(mutable=True),
        "network_helper": Property(mutable=True),
        "last_name": Property(mutable=True),
        "city": Property(mutable=True),
        "state": Property(mutable=True),
        "first_name": Property(mutable=True),
        "phone": Property(mutable=True),
        "managed": Property(),
        "email": Property(mutable=True),
        "zip": Property(mutable=True),
        "address_2": Property(mutable=True),
    }

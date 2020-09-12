from linode_api4.objects import Base, Property


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


class LongviewSubscription(Base):
    api_endpoint = 'longview/subscriptions/{id}'
    properties = {
        "id": Property(identifier=True),
        "label": Property(),
        "clients_included": Property(),
        "price": Property()
    }

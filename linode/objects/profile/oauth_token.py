from linode.objects import Base, Property

class Token(Base):
    api_endpoint = "/profile/tokens/{id}"

    properties = {
        "id": Property(identifier=True),
        "scopes": Property(),
        "label": Property(mutable=True),
        "created": Property(is_datetime=True),
        "token": Property(),
        "expiry": Property(is_datetime=True),
    }

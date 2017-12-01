from linode.objects import Base, Property


class AuthorizedApp(Base):
    api_endpoint = "/profile/apps/{id}"

    properties = {
        "id": Property(identifier=True),
        "scopes": Property(),
        "label": Property(),
        "created": Property(is_datetime=True),
        "expiry": Property(is_datetime=True),
        "thumbnail_url": Property(),
        "website": Property(),
    }

from linode_api4.objects import Base, Property


class Image(Base):
    """
    An Image is something a Linode Instance or Disk can be deployed from.
    """
    api_endpoint = '/images/{id}'

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True),
        "description": Property(mutable=True),
        "status": Property(),
        "created": Property(is_datetime=True),
        "created_by": Property(),
        "type": Property(),
        "is_public": Property(),
        "vendor": Property(),
        "size": Property(),
        "deprecated": Property()
    }

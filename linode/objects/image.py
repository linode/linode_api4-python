from .base import Base, Property

class Image(Base):
    api_endpoint = "/images/{id}"
    properties = {
        'id': Property(identifier=True),
        'label': Property(mutable=True),
        'description': Property(mutable=True),
        'size': Property(),
        'status': Property(),
        'type': Property(),
    }

    def __init__(self, id):
        Base.__init__(self)

        self._set('id', id)

from .base import Base, Property

class Datacenter(Base):
    api_endpoint = "/datacenters/{id}"
    properties = {
        'id': Property(identifier=True),
        'label': Property(),
    }

    def __init__(self, id):
        Base.__init__(self)

        self._set('id', id)

    def __repr__(self):
        return "Datacenter: {}".format(self.id)

from .base import Base, Property

class Distribution(Base):
    api_endpoint = '/distributions'
    properties = {
        'id': Property(identifier=True),
        'label': Property(),
        'minimum_image_size': Property(),
        'recommended': Property(),
        'vendor': Property(),
        'experimental': Property(),
        'created': Property(),
        'x64': Property(),
    }

    def __init__(self, id):
        Base.__init__(self)

        self._set('id', id)

    def __repr__(self):
        return "Distribution: {}".format(self.id)

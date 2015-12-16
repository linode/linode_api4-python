from .base import Base, Property

class Service(Base):
    api_endpoint = "/services/{id}" #TODO - this 404's
    properties = {
        'disk': Property(),
        'hourly_price': Property(),
        'id': Property(identifier=True),
        'label': Property(),
        'mbits_out': Property(),
        'monthly_price': Property(),
        'ram': Property(),
        'service_type': Property(),
        'transfer': Property(),
        'vcpus': Property(),
    }

    def __init__(self, id):
        Base.__init__(self)
       
        self._set('id', id)

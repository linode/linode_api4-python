from .base import Base, Property

class Datacenter(Base):
    api_name = 'datacenters'
    api_endpoint = "/datacenters/{id}"
    properties = {
        'id': Property(identifier=True),
        'label': Property(filterable=True),
    }

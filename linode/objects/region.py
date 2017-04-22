from .base import Base, Property

class Region(Base):
    api_name = 'regions'
    api_endpoint = "/regions/{id}"
    properties = {
        'id': Property(identifier=True),
        'label': Property(filterable=True),
    }

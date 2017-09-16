from .base import Base, Property

class Region(Base):
    api_endpoint = "/regions/{id}"
    properties = {
        'id': Property(identifier=True),
        'country': Property(filterable=True),
    }

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
        'created': Property(is_datetime=True),
        'x64': Property(),
    }

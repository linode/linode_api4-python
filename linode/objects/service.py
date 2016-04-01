from .base import Base, Property

class Service(Base):
    api_endpoint = "/services/{id}" #TODO - this 404's
    properties = {
        'disk': Property(filterable=True),
        'hourly_price': Property(filterable=True),
        'id': Property(identifier=True),
        'label': Property(filterable=True),
        'mbits_out': Property(filterable=True),
        'monthly_price': Property(filterable=True),
        'ram': Property(filterable=True),
        'service_type': Property(filterable=True),
        'transfer': Property(filterable=True),
        'vcpus': Property(filterable=True),
    }

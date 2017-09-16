from .. import Base, Property

class Distribution(Base):
    api_endpoint = '/linode/distributions/{id}'
    properties = {
        'id': Property(identifier=True),
        'label': Property(filterable=True),
        'disk_minimum': Property(filterable=True),
        'deprecated': Property(filterable=True),
        'vendor': Property(filterable=True),
        'updated': Property(is_datetime=True),
        'architecture': Property(filterable=True),
    }

from .. import Base, Property

class Service(Base):
    api_endpoint = "/linode/types/{id}"
    properties = {
        'disk': Property(filterable=True),
        'price_hourly': Property(filterable=True),
        'backups_option': Property(filterable=True),
        'id': Property(identifier=True),
        'label': Property(filterable=True),
        'network_out': Property(filterable=True),
        'price_monthly': Property(filterable=True),
        'memory': Property(filterable=True),
        'transfer': Property(filterable=True),
        'vcpus': Property(filterable=True),
    }

from .base import Base, Property
from .zone_record import ZoneRecord

class Zone(Base):
    api_endpoint = "/zones/{id}"
    properties = {
        'id': Property(identifier=True),
        'zone': Property(mutable=True),
        'display_group': Property(mutable=True),
        'description': Property(mutable=True),
        'status': Property(mutable=True),
        'soa_email': Property(mutable=True),
        'retry_sec': Property(mutable=True),
        'master_ips': Property(mutable=True),
        'axfr_ips': Property(mutable=True),
        'expire_sec': Property(mutable=True),
        'refresh_sec': Property(mutable=True),
        'ttl_se': Property(mutable=True),
        'records': Property(derived_class=ZoneRecord),
    }

    def __init__(self, id):
        Base.__init__(self)

        self._set('id', id)

    def __repr__(self):
        return "Zone: {}".format(self.id)

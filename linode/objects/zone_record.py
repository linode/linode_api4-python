from .dbase import DerivedBase
from .base import Property

class ZoneRecord(DerivedBase):
    api_endpoint = "/zones/{zone_id}/records/{id}"
    derived_url_path = "records"

    properties = {
        'id': Property(identifier=True),
        'zone_id': Property(identifier=True),
        'type': Property(),
        'name': Property(mutable=True),
        'target': Property(mutable=True),
        'priority': Property(mutable=True),
        'weight': Property(mutable=True),
        'port': Property(mutable=True),
        'service': Property(mutable=True),
        'protocol': Property(mutable=True),
        'ttl_sec': Property(mutable=True),
    }

    def __init__(self, id, zone_id):
        DerivedBase.__init__(self, zone_id, parent_id_name='zone_id')

        self._set('id', id)

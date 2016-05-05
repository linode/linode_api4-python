from .dbase import DerivedBase
from .base import Property

class DnsZoneRecord(DerivedBase):
    api_endpoint = "/dnszones/{dns_zone_id}/records/{id}"
    derived_url_path = "records"
    parent_id_name = "dns_zone_id"

    properties = {
        'id': Property(identifier=True),
        'dns_zone_id': Property(identifier=True),
        'zone_record_type': Property(),
        'name': Property(mutable=True, filterable=True),
        'target': Property(mutable=True, filterable=True),
        'priority': Property(mutable=True),
        'weight': Property(mutable=True),
        'port': Property(mutable=True),
        'service': Property(mutable=True),
        'protocol': Property(mutable=True),
        'ttl_sec': Property(mutable=True),
    }

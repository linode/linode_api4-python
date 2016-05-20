from .base import Base, Property
from .dns_zone_record import DnsZoneRecord

class DnsZone(Base):
    api_endpoint = "/dnszones/{id}"
    properties = {
        'id': Property(identifier=True),
        'dnszone': Property(mutable=True, filterable=True),
        'display_group': Property(mutable=True, filterable=True),
        'description': Property(mutable=True),
        'status': Property(mutable=True),
        'soa_email': Property(mutable=True),
        'retry_sec': Property(mutable=True),
        'master_ips': Property(mutable=True, filterable=True),
        'axfr_ips': Property(mutable=True),
        'expire_sec': Property(mutable=True),
        'refresh_sec': Property(mutable=True),
        'ttl_sec': Property(mutable=True),
        'records': Property(derived_class=DnsZoneRecord),
    }

    def create_record(self, record_type, **kwargs):

        params = {
            "type": record_type,
        }
        params.update(kwargs)

        result = self._client.post("{}/records".format(DnsZone.api_endpoint), model=self, data=params)
        self.invalidate()

        if not 'id' in result:
            return result

        zr = DnsZoneRecord(self._client, result['id'], self.id)
        zr._populate(result)
        return zr

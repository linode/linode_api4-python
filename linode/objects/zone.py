from .base import Base, Property
from .zone_record import ZoneRecord

class Zone(Base):
    api_endpoint = "/zones/{id}"
    properties = {
        'id': Property(identifier=True),
        'zone': Property(mutable=True, filterable=True),
        'display_group': Property(mutable=True, filterable=True),
        'description': Property(mutable=True),
        'status': Property(mutable=True),
        'soa_email': Property(mutable=True),
        'retry_sec': Property(mutable=True),
        'master_ips': Property(mutable=True, filterable=True),
        'axfr_ips': Property(mutable=True),
        'expire_sec': Property(mutable=True),
        'refresh_sec': Property(mutable=True),
        'ttl_se': Property(mutable=True),
        'records': Property(derived_class=ZoneRecord),
    }


    def create_record(self, record_type, **kwargs):

        params = {
            "type": record_type,
        }
        params.update(kwargs)

        result = self._client.post("{}/records".format(Zone.api_endpoint), model=self, data=params)
        self.invalidate()

        if not 'record' in result:
            return result

        zr = ZoneRecord(self._client, result['record']['id'], self.id)
        zr._populate(result['record'])
        return zr

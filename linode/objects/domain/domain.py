from __future__ import absolute_import

from linode.errors import UnexpectedResponseError
from linode.objects import Base, Property

from .record import DomainRecord


class Domain(Base):
    api_endpoint = "/domains/{id}"
    properties = {
        'id': Property(identifier=True),
        'domain': Property(mutable=True, filterable=True),
        'group': Property(mutable=True, filterable=True),
        'description': Property(mutable=True),
        'status': Property(mutable=True),
        'soa_email': Property(mutable=True),
        'retry_sec': Property(mutable=True),
        'master_ips': Property(mutable=True, filterable=True),
        'axfr_ips': Property(mutable=True),
        'expire_sec': Property(mutable=True),
        'refresh_sec': Property(mutable=True),
        'ttl_sec': Property(mutable=True),
        'records': Property(derived_class=DomainRecord),
        'type': Property(mutable=True),
    }

    def create_record(self, record_type, **kwargs):

        params = {
            "type": record_type,
        }
        params.update(kwargs)

        result = self._client.post("{}/records".format(Domain.api_endpoint), model=self, data=params)
        self.invalidate()

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response creating domain record!', json=result)

        zr = DomainRecord(self._client, result['id'], self.id, result)
        return zr

from .. import Base, Property
from .. import Linode, StackScript, DnsZone

from random import choice

class Event(Base):
    api_name = 'events'
    api_endpoint = '/account/events/{id}'
    properties = {
        'id': Property(identifier=True),
        'percent_complete': Property(volatile=True),
        'created': Property(is_datetime=True, filterable=True),
        'updated': Property(is_datetime=True, filterable=True),
        'seen': Property(),
        'read': Property(),
        'type': Property(),
        'user_id': Property(),
        'username': Property(),
        'entity': Property(),
        'time_remaining': Property(),
        'rate': Property(),
    }

    @property
    def linode(self):
        if self.entity and self.entity.type == 'linode':
            return Linode(self._client, self.entity.id)
        return None

    @property
    def stackscript(self):
        if self.entity and self.entity.type == 'stackscript':
            return Stackscript(self._client, self.entity.id)
        return None

    @property
    def dnszone(self):
        if self.entity and self.entity.type == 'dnszone':
            return DnsZone(self._client, self.entity.id)
        return None

    @property
    def nodebalancer(self):
        # TODO
        return None

    def mark_read(self):
        self._client.post('{}/read'.format(Event.api_endpoint), model=self)

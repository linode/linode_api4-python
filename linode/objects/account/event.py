from __future__ import absolute_import

from linode.objects import Base, Domain, Linode, Property, StackScript, Volume
from linode.objects.nodebalancer.nodebalancer import NodeBalancer
from linode.objects.support.ticket import SupportTicket


class Event(Base):
    api_endpoint = '/account/events/{id}'
    properties = {
        'id': Property(identifier=True),
        'percent_complete': Property(volatile=True),
        'created': Property(is_datetime=True, filterable=True),
        'updated': Property(is_datetime=True, filterable=True),
        'seen': Property(),
        'read': Property(),
        'action': Property(),
        'user_id': Property(),
        'username': Property(),
        'entity': Property(),
        'time_remaining': Property(),
        'rate': Property(),
        'status': Property(),
    }

    @property
    def linode(self):
        if self.entity and self.entity.type == 'linode':
            return Linode(self._client, self.entity.id)
        return None

    @property
    def stackscript(self):
        if self.entity and self.entity.type == 'stackscript':
            return StackScript(self._client, self.entity.id)
        return None

    @property
    def domain(self):
        if self.entity and self.entity.type == 'domain':
            return Domain(self._client, self.entity.id)
        return None

    @property
    def nodebalancer(self):
        if self.entity and self.entity.type == 'nodebalancer':
            return NodeBalancer(self._client, self.entity.id)
        return None

    @property
    def ticket(self):
        if self.entity and self.entity.type == 'ticket':
            return SupportTicket(self._client, self.entity.id)
        return None

    @property
    def volume(self):
        if self.entity and self.entity.type == 'volume':
            return Volume(self._client, self.entity.id)
        return None

    def mark_read(self):
        self._client.post('{}/read'.format(Event.api_endpoint), model=self)

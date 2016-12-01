from .. import Base, Property
from .. import Linode, StackScript

from random import choice

class Event(Base):
    api_name = 'events'
    api_endpoint = '/account/events/{id}'
    properties = {
        'id': Property(identifier=True),
        'label': Property(),
        'label_message': Property(),
        'status': Property(volatile=True),
        'percent_complete': Property(volatile=True),
        'created': Property(is_datetime=True),
        'finished': Property(is_datetime=True, volatile=True),
        'seen': Property(),
        'read': Property(),
        'linode_id': Property(),
        'stackscript_id': Property(),
        'nodebalancer_id': Property(),
        'event_type': Property(),
    }

    @property
    def linode(self):
        if self.linode_id is not None:
            return Linode(self._client, self.linode_id)
        return None

    @property
    def stackscript(self):
        if self.stackscript_id is not None:
            return Stackscript(self._client, self.stackscript_id)
        return None

    @property
    def nodebalancer(self):
        return None

    def mark_read(self):
        self._client.post('{}/read'.format(Event.api_endpoint), model=self)

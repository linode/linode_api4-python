from __future__ import absolute_import

import requests
from linode.errors import ApiError, UnexpectedResponseError
from linode.objects import Base, Domain, Linode, Property, Volume
from linode.objects.nodebalancer.nodebalancer import NodeBalancer

from .reply import TicketReply


class SupportTicket(Base):
    api_endpoint = '/support/tickets/{id}'
    properties = {
        'id': Property(identifier=True),
        'summary': Property(),
        'description': Property(),
        'status': Property(filterable=True),
        'entity': Property(),
        'opened': Property(is_datetime=True),
        'closed': Property(is_datetime=True),
        'updated': Property(is_datetime=True),
        'updated_by': Property(),
        'replies': Property(derived_class=TicketReply),
    }

    @property
    def linode(self):
        if self.entity and self.entity.type == 'linode':
            return Linode(self._client, self.entity.id)
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
    def volume(self):
        if self.entity and self.entity.type == 'volume':
            return Volume(self._client, self.entity.id)
        return None

    def post_reply(self, description):
        """
        """
        result = self._client.post("{}/replies".format(SupportTicket.api_endpoint), model=self, data={
            "description": description,
        })

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when creating ticket reply!',
                    json=result)

        r = TicketReply(self._client, result['id'], self.id, result)
        return r

    def upload_attachment(self, attachment):
        content = None
        with open(attachment) as f:
            content = f.read()

        if not content:
            raise ValueError('Nothing to upload!')

        headers = {
            "Authorization": "token {}".format(self._client.token),
            "Content-type": "multipart/form-data",
        }

        result = requests.post('{}{}/attachments'.format(self._client.base_url,
                SupportTicket.api_endpoint.format(id=self.id)),
                headers=headers, files=content)

        if not result.status_code == 200:
            errors = []
            j = result.json()
            if 'errors' in j:
                errors = [ e['reason'] for e in j['errors'] ]
            raise ApiError('{}: {}'.format(result.status_code, errors), json=j)

        return True

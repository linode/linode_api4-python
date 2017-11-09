import requests
import os

from .. import Base, Property
from .. import Linode, Domain, Volume
from linode.objects.nodebalancer.nodebalancer import NodeBalancer
from ...errors import ApiError
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
        filename = None
        content = None
        with open(attachment, 'rb') as f:
            filename, content = os.path.basename(f.name), f.read()

        if not content:
            raise ValueError('Nothing to upload!')

        headers = {
            "Authorization": "token {}".format(self._client.token)
        }

        result = requests.post('{}{}/attachments'.format(self._client.base_url,
                SupportTicket.api_endpoint.format(id=self.id)),
                headers=headers, files={'file': (filename, content)})

        if not result.status_code == 200:
            errors = []

            # Try/catch here because we may not get back json if we get an error at the webserver level
            try:
                j = result.json()
            except:
                j = {"errors": [{"reason": "An error has occured."}]}

            if 'errors' in j:
                errors = [ e['reason'] for e in j['errors'] ]
            raise ApiError('{}: {}'.format(result.status_code, errors), json=j)

        return True

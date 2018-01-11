from __future__ import absolute_import

from linode.errors import UnexpectedResponseError
from linode.objects import Base, Property, Region
from linode.objects.networking import IPAddress

from .config import NodeBalancerConfig


class NodeBalancer(Base):
    api_endpoint = '/nodebalancers/{id}'
    properties = {
        'id': Property(identifier=True),
        'label': Property(mutable=True),
        'hostname': Property(),
        'client_conn_throttle': Property(mutable=True),
        'status': Property(),
        'created': Property(is_datetime=True),
        'updated': Property(is_datetime=True),
        'ipv4': Property(relationship=IPAddress),
        'ipv6': Property(),
        'region': Property(slug_relationship=Region, filterable=True),
        'configs': Property(derived_class=NodeBalancerConfig),
    }

    # create derived objects
    def create_config(self, label=None, **kwargs):
        params = kwargs
        if label:
            params['label'] = label

        result = self._client.post("{}/configs".format(NodeBalancer.api_endpoint), model=self, data=params)
        self.invalidate()

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response creating config!', json=result)

        c = NodeBalancerConfig(self._client, result['id'], self.id, result)
        return c

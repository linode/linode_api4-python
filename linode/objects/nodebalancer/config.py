import os

from .. import DerivedBase, Property
from ..base import MappedObject
from .node import NodeBalancerNode

class NodeBalancerConfig(DerivedBase):
    api_name = 'configs'
    api_endpoint = '/nodebalancers/{nodebalancer_id}/configs/{id}'
    derived_url_path = 'configs'
    parent_id_name='nodebalancer_id'

    properties = {
        'id': Property(identifier=True),
        'nodebalancer_id': Property(identifier=True),
        "port": Property(mutable=True),
        "protocol": Property(mutable=True),
        "algorithm": Property(mutable=True),
        "stickiness": Property(mutable=True),
        "check": Property(mutable=True),
        "check_interval": Property(mutable=True),
        "check_timeout": Property(mutable=True),
        "check_attempts": Property(mutable=True),
        "check_path": Property(mutable=True),
        "check_body": Property(mutable=True),
        "check_passive": Property(mutable=True),
        "ssl_cert": Property(mutable=True),
        "ssl_key": Property(mutable=True),
        "cipher_suite": Property(mutable=True),
        "nodes_status": Property(),
    }

    @property
    def nodes(self):
        """
        This is a special derived_class relationship because NodeBalancerNode is the
        only api object that requires two parent_ids
        """
        if not hasattr(self, '_nodes'):
            base_url = "{}/{}".format(NodeBalancerConfig.api_endpoint, NodeBalancerNode.derived_url_path)
            result = self._client._get_objects(base_url, NodeBalancerNode, model=self, parent_id=(self.id, self.nodebalancer_id))

            self._set('_nodes', result)

        return self._nodes

    def create_node(self, label, address, **kwargs):
        params = {
            "label": label,
            "address": address,
        }
        params.update(kwargs)

        result = self._client.post("{}/nodes".format(NodeBalancerConfig.api_endpoint), model=self, data=params)
        self.invalidate()

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response creating node!', json=result)

        n = NodeBalancerNode(self._client, result['id'], self.id, self.nodebalancer_id) # this is three levels deep, so we need a special constructor
        n._populate(result)
        return n

    def enable_ssl(self, cert, key):
        """
        Enables SSL on a NodeBalancer Config (port), served using the given cert and unpassphrased
        key
        """
        params = {}

        params['ssl_cert'] = cert
        if not 'BEGIN CERTIFICATE' in cert:
            # if it doesn't look like a cert, maybe it's a path?
            if os.path.isfile(os.path.expanduser(cert)):
                with open(os.path.expanduser(cert)) as f:
                        params['ssl_cert'] = f.read()

        params['ssl_key'] = key
        if not 'PRIVATE KEY' in key:
            # if it doesn't look like a key, maybe it's a path?
            if os.path.isfile(os.path.expanduser(key)):
                with open(os.path.expanduser(key)) as f:
                        params['ssl_key'] = f.read()

        self._client.post('{}/ssl'.format(NodeBalancerConfig.api_endpoint), model=self, data=params)

        return True

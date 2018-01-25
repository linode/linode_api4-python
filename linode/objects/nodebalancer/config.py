from __future__ import absolute_import

import os

from linode.errors import UnexpectedResponseError
from linode.objects import DerivedBase, Property

from .node import NodeBalancerNode


class NodeBalancerConfig(DerivedBase):
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
        "ssl_commonname": Property(),
        "ssl_fingerprint": Property(),
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

        # this is three levels deep, so we need a special constructor
        n = NodeBalancerNode(self._client, result['id'], self.id, self.nodebalancer_id, result)
        return n

    def load_ssl_data(self, cert_file, key_file):
        """
        A convenience method that loads a cert and a key from files and sets them
        on this object.  This can make enabling ssl easier (instead of you needing
        to load the files yourself).

        This does *not* change protocol/port for you, or save anything.  Once this
        is called, you must still call `save()` on this object for the changes to
        take effect.

        :param cert_file: A path to the file containing the public certificate
        :type cert_file: str
        :param key_file: A path to the file containing the unpassphrased private key
        :type key_file: str
        """
        # we're disabling warnings here because these attributes are defined dynamically
        # through linode.objects.Base, and pylint isn't privy
        if os.path.isfile(os.path.expanduser(cert_file)):
            with open(os.path.expanduser(cert_file)) as f:
                self.ssl_cert = f.read() # pylint: disable=attribute-defined-outside-init

        if os.path.isfile(os.path.expanduser(key_file)):
            with open(os.path.expanduser(key_file)) as f:
                self.ssl_key = f.read() # pylint: disable=attribute-defined-outside-init

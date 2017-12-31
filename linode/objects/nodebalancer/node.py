from __future__ import absolute_import

from linode.objects import DerivedBase, Property


class NodeBalancerNode(DerivedBase):
    api_endpoint = '/nodebalancers/{nodebalancer_id}/configs/{config_id}/nodes/{id}'
    derived_url_path = 'nodes'
    parent_id_name='config_id'

    properties = {
        'id': Property(identifier=True),
        'config_id': Property(identifier=True),
        'nodebalancer_id': Property(identifier=True),
        "label": Property(mutable=True),
        "address": Property(mutable=True),
        "weight": Property(mutable=True),
        "mode": Property(mutable=True),
        "status": Property(),
    }

    def __init__(self, client, id, parent_id, nodebalancer_id=None, json=None):
        """
        We need a special constructor here because this object's parent
        has a parent itself.
        """
        if not nodebalancer_id and not isinstance(parent_id, tuple):
            raise ValueError('NodeBalancerNode must either be created with a nodebalancer_id or a tuple of '
                    '(config_id, nodebalancer_id) for parent_id!')

        if isinstance(parent_id, tuple):
            nodebalancer_id = parent_id[1]
            parent_id = parent_id[0]

        DerivedBase.__init__(self, client, id, parent_id, json=json)

        self._set('nodebalancer_id', nodebalancer_id)

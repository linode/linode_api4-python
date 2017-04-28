from .. import DerivedBase, Property
from ..base import MappedObject

class NodeBalancerNode(DerivedBase):
    api_name = 'nodes'
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

    def __init__(self, client, id, parent_id, nodebalancer_id):
        """
        We need a special constructor here because this object's parent
        has a parent itself.
        """
        DerivedBase.__init__(self, client, id, parent_id)

        self._set('nodebalancer_id', nodebalancer_id)

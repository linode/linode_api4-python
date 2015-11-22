from .dbase import DerivedBase
from .base import Property

class Disk(DerivedBase):
    api_endpoint = '/linodes/{linode_id}/disks/{id}'
    derived_url_path = 'disks'

    properties = {
        'id': Property(identifier=True),
        'created': Property(),
        'label': Property(mutable=True),
        'size': Property(),
        'status': Property(),
        'type': Property(),
        'updated': Property(),
        'linode_id': Property(identifier=True),
    }

    def __init__(self, id, linode_id):
        DerivedBase.__init__(self, linode_id, parent_id_name='linode_id')

        self._set('id', id)

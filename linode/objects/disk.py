from .dbase import DerivedBase
from .base import Property

class Disk(DerivedBase):
    api_endpoint = '/linodes/{linode_id}/disks/{id}'
    derived_url_path = 'disks'
    parent_id_name='linode_id'

    properties = {
        'id': Property(identifier=True),
        'created': Property(is_datetime=True),
        'label': Property(mutable=True),
        'size': Property(),
        'status': Property(),
        'type': Property(),
        'updated': Property(is_datetime=True),
        'linode_id': Property(identifier=True),
    }

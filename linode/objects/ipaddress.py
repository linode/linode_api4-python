from .dbase import DerivedBase
from .base import Property

class IPAddress(DerivedBase):
    api_name = 'ips'
    api_endpoint = '/linodes/{linode_id}/ips/{id}'
    derived_url_path = 'ips'
    parent_id_name='linode_id'

    properties = {
        'id': Property(identifier=True),
        'linode_id': Property(identifier=True),
        'address': Property(),
        'rdns': Property(mutable=True),
        'type': Property(filterable=True),
    }

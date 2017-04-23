from .. import DerivedBase, Property
from ..base import MappedObject

class NodeBalancerConfig(DerivedBase):
    api_name = 'configs'
    api_endpoint = '/nodebalancers/{nodebalancer_id}/configs/{id}'
    derived_url_path = 'configs'
    parent_id_name='nodebalancer_id'

    properties = {
        'id': Property(identifier=True),
        'nodebalancer_id': Property(identifier=True),
        "label": Property(mutable=True),
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
    }

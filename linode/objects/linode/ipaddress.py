from .. import DerivedBase, Property

class IPAddress(DerivedBase):
    api_name = 'ips'
    api_endpoint = '/linode/instances/{linode_id}/ips/{id}'
    derived_url_path = 'ips'
    parent_id_name='linode_id'

    properties = {
        'id': Property(identifier=True),
        'linode_id': Property(identifier=True),
        'address': Property(),
        'rdns': Property(mutable=True),
        'type': Property(filterable=True),
    }

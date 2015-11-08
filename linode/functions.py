from linode import api
from linode.objects import Linode

def get_distributions():
    return api.get_objects('/distributions', 'distributions')

def get_services():
    return api.get_objects('/services', 'services')

def get_datacenters():
    return api.get_objects('/datacenters', 'datacenters')

def get_linodes():
    return api.get_objects('/linodes', 'linodes')

def create_linode(service, datacenter, source=None, opts={}):
    if not 'linode' in service.service_type:
        raise AttributeError("{} is not a linode service!".format(service.label))

    params = {
         'service': service.id,
         'datacenter': datacenter.id,
         'source': source.id if source else None,
     }
    params.update(opts)

    result = api.api_call('/linodes', method='POST', data=params)

    if not 'linode' in result:
        return result

    l = Linode(result['linode']['id'])
    l._populate(result['linode'])
    return l

from linode import api
from linode.objects import Base, Linode

def filter_list(results, **filter_by):
    if not results or not len(results):
        return results

    if not filter_by or not len(filter_by):
        return results

    for key in filter_by.keys():
        if not key in vars(results[0]):
            raise ValueError("Cannot filter {} by {}".format(type(results[0]), key))
        if isinstance(vars(results[0])[key], Base) and isinstance(filter_by[key], Base):
            results = [ r for r in results if vars(r)[key].id == filter_by[key].id ]
        elif isinstance(vars(results[0])[key], str) and isinstance(filter_by[key], str):
            results = [ r for r in results if filter_by[key].lower() in vars(r)[key].lower()  ]
        else:
            results = [ r for r in results if vars(r)[key] == filter_by[key] ]

    return results

def get(obj_type, **filters):
    results = api.get_objects("/{}".format(obj_type), obj_type)

    if filters and len(filters):
        results = filter_list(results, **filters)

    return results

def get_distributions(**filters):
    return get('distributions', **filters)

def get_services(**filters):
    return get('services', **filters)

def get_datacenters(**filters):
    return get('datacenters', **filters)

def get_linodes(**filters):
    return get('linodes', **filters)

def get_stackscripts(**filters):
    return get('stackscripts', **filters)

def create_linode(service, datacenter, source=None, **kwargs):
    if not 'linode' in service.service_type:
        raise AttributeError("{} is not a linode service!".format(service.label))

    params = {
         'service': service.id,
         'datacenter': datacenter.id,
         'source': source.id if source else None,
     }
    params.update(kwargs)

    result = api.api_call('/linodes', method='POST', data=params)

    if not 'linode' in result:
        return result

    l = Linode(result['linode']['id'])
    l._populate(result['linode'])
    return l

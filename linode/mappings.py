import linode.objects
from linode import util


def get_mapping(id):
    id_map = { 
        'lnde': linode.objects.Linode,
        'disk': linode.objects.Disk,
        'dist': linode.objects.Distribution,
        'serv': linode.objects.Service,
        'dctr': linode.objects.Datacenter,
        'stck': linode.objects.StackScript,
    }

    parts = id.split('_')

    if not len(parts) == 2:
        return False

    if parts[0] in id_map:
        return id_map[parts[0]]
    return None

def make(id):
    """
    Makes an api object based on an id.  The type depends on the mapping.
    """
    c = get_mapping(id)

    if c:
        return c(id)
    return None

def make_list(json_arr):
    result = []

    for obj in json_arr:
        if not 'id' in obj:
            continue
        o = make(obj['id'])
        o._populate(obj)
        result.append(o)

    return result

def make_paginated_list(json, key):
    l = make_list(json[key])
    p = util.PaginatedList(key, page=l, max_pages=json['total_pages'], \
         total_items=json['total_results'])

    return p

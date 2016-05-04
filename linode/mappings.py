import linode.objects
from linode import util


def get_mapping(id):
    id_map = { 
        'linode': linode.objects.Linode,
        'disk': linode.objects.Disk,
        'distro': linode.objects.Distribution,
        'service': linode.objects.Service,
        'datacenter': linode.objects.Datacenter,
        'stackscript': linode.objects.StackScript,
        'config': linode.objects.Config,
        'kernel': linode.objects.Kernel,
        'dnszone': linode.objects.DnsZone,
        'dnsrecord': linode.objects.DnsZoneRecord,
    }

    parts = id.split('_')

    if not len(parts) == 2:
        return False

    if parts[0] in id_map:
        return id_map[parts[0]]
    return None

def make(id, client, parent_id=None):
    """
    Makes an api object based on an id.  The type depends on the mapping.
    """
    c = get_mapping(id)

    if c:
        if issubclass(c, linode.objects.DerivedBase):
            return c(client, id, parent_id)
        else:
            return c(client, id)
    return None

def make_list(json_arr, client, parent_id=None):
    result = []

    for obj in json_arr:
        if not 'id' in obj:
            continue
        o = make(obj['id'], client, parent_id=parent_id)
        o._populate(obj)
        result.append(o)

    return result

def make_paginated_list(json, key, client, parent_id=None, page_url=None):
    l = make_list(json[key], client, parent_id=parent_id)
    p = util.PaginatedList(client, page_url if page_url else key, page=l, \
         max_pages=json['total_pages'],  total_items=json['total_results'], parent_id=parent_id, \
         key=key)
    return p

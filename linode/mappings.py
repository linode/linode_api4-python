import linode.objects
from linode import util

def make(id, client, parent_id=None, cls=None):
    """
    Makes an api object based on an id.  The type depends on the mapping.
    """
    if cls:
        if issubclass(cls, linode.objects.DerivedBase):
            return cls(client, id, parent_id)
        else:
            return cls(client, id)
    return None

def make_list(json_arr, client, parent_id=None, cls=None):
    result = []

    for obj in json_arr:
        if not 'id' in obj:
            continue
        o = make(obj['id'], client, parent_id=parent_id, cls=cls)
        o._populate(obj)
        result.append(o)

    return result

def make_paginated_list(json, key, client, parent_id=None, page_url=None, cls=None):
    l = make_list(json[key], client, parent_id=parent_id, cls=cls)
    p = util.PaginatedList(client, page_url if page_url else key, page=l, \
         max_pages=json['total_pages'],  total_items=json['total_results'], parent_id=parent_id, \
         key=key)
    return p

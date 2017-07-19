from linode import util

def make(id, client, parent_id=None, cls=None):
    """
    Makes an api object based on an id.  The type depends on the mapping.
    """
    from linode.objects import DerivedBase
    if cls:
        if issubclass(cls, DerivedBase):
            return cls(client, id, parent_id)
        else:
            return cls(client, id)
    return None

def make_list(json_arr, client, parent_id=None, cls=None):
    result = []

    for obj in json_arr:
        id_val = None

        if 'id' in obj:
            id_val = obj['id']
        elif hasattr(cls, 'id_attribute') and getattr(cls, 'id_attribute') in obj:
            id_val = obj[getattr(cls, 'id_attribute')]
        else:
            continue
        o = make(id_val, client, parent_id=parent_id, cls=cls)
        o._populate(obj)
        result.append(o)

    return result

def make_paginated_list(json, key, client, parent_id=None, page_url=None, cls=None):
    l = make_list(json[key], client, parent_id=parent_id, cls=cls)
    p = util.PaginatedList(client, page_url if page_url else key, page=l, \
         max_pages=json['total_pages'],  total_items=json['total_results'], parent_id=parent_id, \
         key=key)
    return p

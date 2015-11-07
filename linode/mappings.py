import linode.objects


def get_mapping(id):
    id_map = { 
        'lnde': linode.objects.Linode,
        'disk': linode.objects.Disk,
        'dist': linode.objects.Distribution,
        'serv': linode.objects.Service,
        'dctr': linode.objects.Datacenter,
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

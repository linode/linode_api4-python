
normal_grants = ('all','access','delete')
stackscript_grants = ('all','use','edit','delete')
linode_grants = ('all','access','delete','resize')

def get_obj_grants():
    """
    Returns Grant keys mapped to Object types.
    """
    from linode.objects import (Base, DerivedBase, Linode, Domain, StackScript,
            NodeBalancer, Volume)
    return ( ('linode', Linode), ('domain', Domain), ('stackscript', StackScript),
        ('nodebalancer', NodeBalancer), ('volumes', Volume) )

class Grant:
    def __init__(self, client, cls, dct):
        self._client = client
        self.cls = cls
        self.id = dct['id']
        self.label = dct['label']
        self.grants = normal_grants
        if cls is Linode:
            self.grants = linode_grants
        elif cls is StackScript:
            self.grants = stackscript_grants

        for g in self.grants:
            setattr(self, g, dct[g])

    @property
    def entity(self):
        # there are no grants for derived types, so this shouldn't happen
        if not issubclass(self.cls, Base) or issubclass(self.cls, DerivedBase):
            raise ValueError("Cannot get entity for non-base-class {}".format(self.cls))
        return self.cls(self._client, self.id)

    def _serialize(self):
        """
        Returns this grant in a PUT-able form
        """
        ret = { g: getattr(self, g) for g in self.grants }
        ret['id'] = self.id
        return ret

class UserGrants:
    api_endpoint = "/account/users/{username}/grants"
    parent_id_name = 'username'

    def __init__(self, client, username):
        self._client = client
        self.username = username
    
    def _populate(self, json):
        self.global_grants = type('global_grants', (object,), json['global'])
        self.customer = type('customer_grants', (object,), json['customer'])

        for key, cls in get_obj_grants():
            lst = []
            for gdct in json[key]:
                lst.append(Grant(self._client, cls, gdct))
            setattr(self, key, lst)

    def save(self):
        req = {
            'global': { k: v for k,v in vars(self.global_grants).items() if not k.startswith('_') },
            'customer': { k: v for k,v in vars(self.customer).items() if not k.startswith('_') },
        }

        for key, _ in get_obj_grants():
            lst = []
            for cg in getattr(self, key):
                lst.append(cg._serialize())
            req[key] = lst
        print(req)

        result = self._client.put(UserGrants.api_endpoint.format(username=self.username), data=req)

        self._populate(result)

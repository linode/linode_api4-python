from __future__ import absolute_import

from linode.objects.base import Base
from linode.objects.dbase import DerivedBase
from linode.objects.domain import Domain
from linode.objects.linode import Linode, StackScript
from linode.objects.longview import LongviewClient
from linode.objects.nodebalancer import NodeBalancer
from linode.objects.volume import Volume

normal_grants = ('all', 'access', 'delete')
stackscript_grants = ('all', 'use', 'edit', 'delete')
linode_grants = ('all', 'access', 'delete', 'resize')


def get_obj_grants():
    """
    Returns Grant keys mapped to Object types.
    """
    return (('linode', Linode),
            ('domain', Domain),
            ('stackscript', StackScript),
            ('nodebalancer', NodeBalancer),
            ('volume', Volume),
            #('image', Image),
            ('longview', LongviewClient))


class Grant:
    """
    A Grant is a single grant a user has to an object.  A Grant's entity is
    an object on the account, such as a Linode, NodeBalancer, or Volume, and
    its permissions level is one of None, "read_only" or "read_write".

    Grants cannot be accessed or updated individually, and are only relevant in
    the context of a UserGrants object.
    """
    def __init__(self, client, cls, dct):
        self._client = client
        self.cls = cls
        self.id = dct['id']
        self.label = dct['label']
        self.permissions = dct['permissions']

    @property
    def entity(self):
        """
        Returns the object this grant is for.  The objects type depends on the
        type of object this grant is applied to, and the object returned is
        not populated (accessing its attributes will trigger an api request).

        :returns: This grant's entity
        :rtype: Linode, NodeBalancer, Domain, StackScript, Volume, or Longview
        """
        # there are no grants for derived types, so this shouldn't happen
        if not issubclass(self.cls, Base) or issubclass(self.cls, DerivedBase):
            raise ValueError("Cannot get entity for non-base-class {}".format(self.cls))
        return self.cls(self._client, self.id)

    def _serialize(self):
        """
        Returns this grant in as JSON the api will accept.  This is only relevant
        in the context of UserGrants.save
        """
        return {
            'permissions': self.permissions,
            'id': self.id
        }


class UserGrants:
    """
    The UserGrants object represents the grants given to a restricted user.
    Each section of grants has a list of objects and the level of grants this
    user has to that object.

    This is not an instance of Base because it lacks most of the attributes of
    a Base-like model (such as a unique, ID-based endpoint at which to access
    it), however it has some similarities so that its usage is familiar.
    """
    api_endpoint = "/account/users/{username}/grants"
    parent_id_name = 'username'

    def __init__(self, client, username, json=None):
        self._client = client
        self.username = username

        if json is not None:
            self._populate(json)
    
    def _populate(self, json):
        self.global_grants = type('global_grants', (object,), json['global'])

        for key, cls in get_obj_grants():
            lst = []
            for gdct in json[key]:
                lst.append(Grant(self._client, cls, gdct))
            setattr(self, key, lst)

    def save(self):
        req = {
            'global': {k: v for k, v in vars(self.global_grants).items() if not k.startswith('_')},
        }

        for key, _ in get_obj_grants():
            lst = []
            for cg in getattr(self, key):
                lst.append(cg._serialize())
            req[key] = lst

        result = self._client.put(UserGrants.api_endpoint.format(username=self.username), data=req)

        self._populate(result)

        return True

from datetime import datetime
import requests

from linode_api4.errors import ApiError, UnexpectedResponseError
from linode_api4.objects import (Base, DerivedBase, Domain, Image, Instance,
                                 Property, StackScript, Volume, DATE_FORMAT)
from linode_api4.objects.longview import LongviewClient, LongviewSubscription
from linode_api4.objects.nodebalancer import NodeBalancer
from linode_api4.objects.support import SupportTicket

class Account(Base):
    api_endpoint = "/account"
    id_attribute = 'email'

    properties = {
        "company": Property(mutable=True),
        "country": Property(mutable=True),
        "balance": Property(),
        "address_1": Property(mutable=True),
        "last_name": Property(mutable=True),
        "city": Property(mutable=True),
        "state": Property(mutable=True),
        "first_name": Property(mutable=True),
        "phone": Property(mutable=True),
        "email": Property(mutable=True),
        "zip": Property(mutable=True),
        "address_2": Property(mutable=True),
        "tax_id": Property(mutable=True),
        "capabilities": Property(),
        'credit_card': Property(),
    }


class AccountSettings(Base):
    api_endpoint = "/account/settings"
    id_attribute = 'managed' # this isn't actually used

    properties = {
        "network_helper": Property(mutable=True),
        "managed": Property(),
        "longview_subscription": Property(slug_relationship=LongviewSubscription),
        "object_storage": Property(),
    }


class Event(Base):
    api_endpoint = '/account/events/{id}'
    properties = {
        'id': Property(identifier=True, filterable=True),
        'percent_complete': Property(volatile=True),
        'created': Property(is_datetime=True, filterable=True),
        'updated': Property(is_datetime=True, filterable=True),
        'seen': Property(),
        'read': Property(),
        'action': Property(),
        'user_id': Property(),
        'username': Property(),
        'entity': Property(),
        'time_remaining': Property(),
        'rate': Property(),
        'status': Property(),
    }

    @property
    def linode(self):
        if self.entity and self.entity.type == 'linode':
            return Instance(self._client, self.entity.id)
        return None

    @property
    def stackscript(self):
        if self.entity and self.entity.type == 'stackscript':
            return StackScript(self._client, self.entity.id)
        return None

    @property
    def domain(self):
        if self.entity and self.entity.type == 'domain':
            return Domain(self._client, self.entity.id)
        return None

    @property
    def nodebalancer(self):
        if self.entity and self.entity.type == 'nodebalancer':
            return NodeBalancer(self._client, self.entity.id)
        return None

    @property
    def ticket(self):
        if self.entity and self.entity.type == 'ticket':
            return SupportTicket(self._client, self.entity.id)
        return None

    @property
    def volume(self):
        if self.entity and self.entity.type == 'volume':
            return Volume(self._client, self.entity.id)
        return None

    def mark_read(self):
        self._client.post('{}/read'.format(Event.api_endpoint), model=self)


class InvoiceItem(DerivedBase):
    api_endpoint = '/account/invoices/{invoice_id}/items'
    derived_url_path = 'items'
    parent_id_name='invoice_id'
    id_attribute = 'label' # this has to be something

    properties = {
        'invoice_id': Property(identifier=True),
        'unit_price': Property(),
        'label': Property(),
        'amount': Property(),
        'quantity': Property(),
        #'from_date': Property(is_datetime=True), this is populated below from the "from" attribute
        'to': Property(is_datetime=True),
        #'to_date': Property(is_datetime=True), this is populated below from the "to" attribute
        'type': Property(),
    }

    def _populate(self, json):
        """
        Allows population of "from_date" from the returned "from" attribute which
        is a reserved word in python.  Also populates "to_date" to be complete.
        """
        super()._populate(json)

        self.from_date = datetime.strptime(json['from'], DATE_FORMAT)
        self.to_date = datetime.strptime(json['to'], DATE_FORMAT)


class Invoice(Base):
    api_endpoint = "/account/invoices/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(),
        "date": Property(is_datetime=True),
        "total": Property(),
        "items": Property(derived_class=InvoiceItem),
    }


class OAuthClient(Base):
    api_endpoint = "/account/oauth-clients/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True, filterable=True),
        "secret": Property(),
        "redirect_uri": Property(mutable=True),
        "status": Property(),
        "public": Property(),
    }

    def reset_secret(self):
        """
        Resets the client secret for this client.
        """
        result = self._client.post("{}/reset_secret".format(OAuthClient.api_endpoint), model=self)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when resetting secret!', json=result)

        self._populate(result)
        return self.secret

    def thumbnail(self, dump_to=None):
        """
        This returns binary data that represents a 128x128 image.
        If dump_to is given, attempts to write the image to a file
        at the given location.
        """
        headers = {
            "Authorization": "token {}".format(self._client.token)
        }

        result = requests.get('{}/{}/thumbnail'.format(self._client.base_url,
                OAuthClient.api_endpoint.format(id=self.id)),
                headers=headers)

        if not result.status_code == 200:
            raise ApiError('No thumbnail found for OAuthClient {}'.format(self.id))

        if dump_to:
            with open(dump_to, 'wb+') as f:
                f.write(result.content)
        return result.content

    def set_thumbnail(self, thumbnail):
        """
        Sets the thumbnail for this OAuth Client.  If thumbnail is bytes,
        uploads it as a png.  Otherwise, assumes thumbnail is a path to the
        thumbnail and reads it in as bytes before uploading.
        """
        headers = {
            "Authorization": "token {}".format(self._client.token),
            "Content-type": "image/png",
        }

        # TODO this check needs to be smarter - python2 doesn't do it right
        if not isinstance(thumbnail, bytes):
            with open(thumbnail, 'rb') as f:
                thumbnail = f.read()

        result = requests.put('{}/{}/thumbnail'.format(self._client.base_url,
                OAuthClient.api_endpoint.format(id=self.id)),
                headers=headers, data=thumbnail)

        if not result.status_code == 200:
            errors = []
            j = result.json()
            if 'errors' in j:
                errors = [ e['reason'] for e in j['errors'] ]
            raise ApiError('{}: {}'.format(result.status_code, errors), json=j)

        return True


class Payment(Base):
    api_endpoint = "/account/payments/{id}"

    properties = {
        "id": Property(identifier=True),
        "date": Property(is_datetime=True),
        "amount": Property(),
    }


class User(Base):
    api_endpoint = "/account/users/{id}"
    id_attribute = 'username'

    properties = {
        'email': Property(),
        'username': Property(identifier=True, mutable=True),
        'restricted': Property(mutable=True),
    }

    @property
    def grants(self):
        """
        Retrieves the grants for this user.  If the user is unrestricted, this
        will result in an ApiError.  This is smart, and will only fetch from the
        api once unless the object is invalidated.

        :returns: The grants for this user.
        :rtype: linode.objects.account.UserGrants
        """
        from linode_api4.objects.account import UserGrants # pylint: disable-all
        if not hasattr(self, '_grants'):
            resp = self._client.get(UserGrants.api_endpoint.format(username=self.username))

            grants = UserGrants(self._client, self.username, resp)
            self._set('_grants', grants)

        return self._grants

    def invalidate(self):
        if hasattr(self, '_grants'):
            del self._grants
        Base.invalidate(self)


def get_obj_grants():
    """
    Returns Grant keys mapped to Object types.
    """
    return (('linode', Instance),
            ('domain', Domain),
            ('stackscript', StackScript),
            ('nodebalancer', NodeBalancer),
            ('volume', Volume),
            ('image', Image),
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

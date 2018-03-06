from __future__ import absolute_import

import json
import logging
from datetime import datetime

import pkg_resources
import requests
from linode.errors import ApiError, UnexpectedResponseError
from linode.objects import *
from linode.objects.filtering import Filter

from .common import load_and_validate_keys
from .paginated_list import PaginatedList

package_version = pkg_resources.require("linode-api")[0].version

logger = logging.getLogger(__name__)


class Group:
    def __init__(self, client):
        self.client = client


class LinodeGroup(Group):
    def get_types(self, *filters):
        return self.client._get_and_filter(Type, *filters)

    def get_instances(self, *filters):
        return self.client._get_and_filter(Linode, *filters)

    def get_stackscripts(self, *filters, **kwargs):
        # python2 can't handle *args and a single keyword argument, so this is a workaround
        if 'mine_only' in kwargs:
            if kwargs['mine_only']:
                new_filter = Filter({"mine":True})
                if filters:
                    filters = [ f for f in filters ]
                    filters[0] = filters[0] & new_filter
                else:
                    filters = [new_filter]

            del kwargs['mine_only']

        if kwargs:
            raise TypeError("get_stackscripts() got unexpected keyword argument '{}'".format(kwargs.popitem()[0]))

        return self.client._get_and_filter(StackScript, *filters)

    def get_kernels(self, *filters):
        return self.client._get_and_filter(Kernel, *filters)

    # create things
    def create_instance(self, ltype, region, image=None,
            authorized_keys=None, **kwargs):
        """
        Creates a new Linode.  This takes a number of parameters in **kwargs
        that are not listed explictly, but will be passed through to the api as
        provided.  For complete details, see the API documentation at
        developers.linode.com

        :param ltype: The Linode Type we are creating
        :param region: The Region in which we are creating the Linode
        :param image: The image to deploy to this Linode
        :param authorized_keys: The ssh public keys to install on the linode's
                                /root/.ssh/authorized_keys file
        :param **kwargs: Any other fields to pass to the api

        :returns: A new Linode object
        :raises ApiError: If contacting the API fails
        :raises UnexpectedResponseError: If the API resposne is somehow malformed.
                                         This usually indicates that you are using
                                         an outdated library.
        """
        ret_pass = None
        if image and not 'root_pass' in kwargs:
            ret_pass = Linode.generate_root_password()
            kwargs['root_pass'] = ret_pass

        authorized_keys = load_and_validate_keys(authorized_keys)

        params = {
             'type': ltype.id if issubclass(type(ltype), Base) else ltype,
             'region': region.id if issubclass(type(region), Base) else region,
             'image': (image.id if issubclass(type(image), Base) else image) if image else None,
             'authorized_keys': authorized_keys,
         }
        params.update(kwargs)

        result = self.client.post('/linode/instances', data=params)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when creating linode!', json=result)

        l = Linode(self.client, result['id'], result)
        if not ret_pass:
            return l
        return l, ret_pass

    def create_stackscript(self, label, script, images, desc=None, public=False, **kwargs):
        image_list = None
        if type(images) is list or type(images) is PaginatedList:
            image_list = [d.id if issubclass(type(d), Base) else d for d in images ]
        elif type(images) is Image:
            image_list = [images.id]
        elif type(images) is str:
            image_list = [images]
        else:
            raise ValueError('images must be a list of Images or a single Image')

        script_body = script
        if not script.startswith("#!"):
            # it doesn't look like a stackscript body, let's see if it's a file
            import os
            if os.path.isfile(script):
                with open(script) as f:
                    script_body = f.read()
            else:
                raise ValueError("script must be the script text or a path to a file")

        params = {
            "label": label,
            "image": image_list,
            "is_public": public,
            "script": script_body,
            "description": desc if desc else '',
        }
        params.update(kwargs)

        result = self.client.post('/linode/stackscripts', data=params)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when creating StackScript!', json=result)

        s = StackScript(self.client, result['id'], result)
        return s


class ProfileGroup(Group):
    """
    Collections related to your user.
    """
    def get_tokens(self, *filters):
        """
        Returns the Person Access Tokens active for this user
        """
        return self.client._get_and_filter(PersonalAccessToken, *filters)

    def create_personal_access_token(self, label=None, expiry=None, scopes=None, **kwargs):
        """
        Creates and returns a new Personal Access Token
        """
        if label:
            kwargs['label'] = label
        if expiry:
            if isinstance(expiry, datetime):
                expiry = datetime.strftime(expiry, "%Y-%m-%dT%H:%M:%S")
            kwargs['expiry'] = expiry
        if scopes:
            kwargs['scopes'] = scopes

        result = self.client.post('/account/tokens', data=kwargs)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when creating Personal Access '
                    'Token!', json=result)

        token = PersonalAccessToken(self.client, result['id'], result)
        return token

    def get_apps(self, *filters):
        """
        Returns the Authorized Applications for this user
        """
        return self.client._get_and_filter(AuthorizedApp, *filters)


class LongviewGroup(Group):
    def get_clients(self, *filters):
        """
        Requests and returns a paginated list of LongviewClients on your
        account.
        """
        return self.client._get_and_filter(LongviewClient, *filters)

    def create_client(self, label=None):
        """
        Creates a new LongviewClient, optionally with a given label.

        :param label: The label for the new client.  If None, a default label based
            on the new client's ID will be used.

        :returns: A new LongviewClient

        :raises ApiError: If a non-200 status code is returned
        :raises UnexpectedResponseError: If the returned data from the api does
            not look as expected.
        """
        result = self.client.post('/longview/clients', data={
            "label": label
        })

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when creating Longivew '
                'Client!', json=result)

        c = LongviewClient(self.client, result['id'], result)
        return c

    def get_subscriptions(self, *filters):
        """
        Requests and returns a paginated list of LongviewSubscriptions available
        """
        return self.client._get_and_filter(LongviewSubscription, *filters)


class AccountGroup(Group):
    def get_events(self, *filters):
        return self.client._get_and_filter(Event, *filters)

    def mark_last_seen_event(self, event):
        """
        Marks event as the last event we have seen.  If event is an int, it is treated
        as an event_id, otherwise it should be an event object whose id will be used.
        """
        last_seen = event if isinstance(event, int) else event.id
        self.client.post('{}/seen'.format(Event.api_endpoint), model=Event(self.client, last_seen))

    def get_settings(self):
        """
        Resturns the account settings data for this acocunt.  This is not  a
        listing endpoint.
        """
        result = self.client.get('/account/settings')

        if not 'managed' in result:
            raise UnexpectedResponseError('Unexpected response when getting account settings!',
                    json=result)

        s = AccountSettings(self.client, result['managed'], result)
        return s

    def get_invoices(self):
        """
        Returns Invoices issued to this account
        """
        return self.client._get_and_filter(Invoice)

    def get_payments(self):
        """
        Returns a list of Payments made to this account
        """
        return self.client._get_and_filter(Payment)

    def get_oauth_clients(self, *filters):
        """
        Returns the OAuth Clients associated to this account
        """
        return self.client._get_and_filter(OAuthClient, *filters)

    def create_oauth_client(self, name, redirect_uri, **kwargs):
        """
        Make a new OAuth Client and return it
        """
        params = {
            "label": name,
            "redirect_uri": redirect_uri,
        }
        params.update(kwargs)

        result = self.client.post('/account/oauth-clients', data=params)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when creating OAuth Client!',
                    json=result)

        c = OAuthClient(self.client, result['id'], result)
        return c

    def get_users(self, *filters):
        """
        Returns a list of users on this account
        """
        return self.client._get_and_filter(User, *filters)

    def get_transfer(self):
        """
        Returns a MappedObject containing the account's transfer pool data
        """
        result = self.client.get('/account/transfer')

        if not 'used' in result:
            raise UnexpectedResponseError('Unexpected response when getting Transfer Pool!')

        return MappedObject(**result)

def create_user(self, email, username, password, restricted=True):
    """
    Creates a user
    """
    params = {
        "email": email,
        "username": username,
        "password": password,
        "restricted": restricted
    }
    result = self.client.post('/account/users', data=params)

    if not 'email' and 'restricted' and 'username' in result:
        raise UnexpectedResponseError('Unexpected response when creating user!', json=result)

    u = User(self.client, result['username'], result)
    return u

class NetworkingGroup(Group):
    def get_ips(self, *filters):
        return self.client._get_and_filter(IPAddress, *filters)

    def get_ipv6_ranges(self, *filters):
        return self.client._get_and_filter(IPv6Range, *filters)

    def get_ipv6_pools(self, *filters):
        return self.client._get_and_filter(IPv6Pool, *filters)

    def assign_ips(self, region, *assignments):
        """
        This takes a set of IPv4 Assignments and moves the IPs where they were
        asked to go.  Call this with any number of IPAddress.to(Linode) results

        For example, swapping ips between linode1 and linode2 might look like this:
            client.networking.assign_ips('newark', ip1.to(linode2), ip2.to(linode1))

        """
        for a in assignments:
            if not 'address' in a or not 'linode_id' in a:
                raise ValueError("Invalid assignment: {}".format(a))
        if isinstance(region, Region):
            region = region.id

        result = self.client.post('/networking/ip-assign', data={
            "region": region,
            "assignments": [ a for a in assignments ],
        })

        if not 'ips' in result:
            raise UnexpectedResponseError('Unexpected response when assigning IPs!',
                    json=result)

        ips = []
        for r in result['ips']:
            i = IPAddress(self.client, r['address'], result)
            ips.append(i)

        return ips

    def allocate_ip(self, linode):
        result = self.client.post('/networking/ipv4/', data={
            "linode_id": linode.id if isinstance(linode, Base) else linode,
        })

        if not 'address' in result:
            raise UnexpectedResponseError('Unexpected response when adding IPv4 address!',
                    json=result)

        ip = IPAddress(self.client, result['address'], result)
        return ip

class SupportGroup(Group):
    def get_tickets(self, *filters):
        return self.client._get_and_filter(SupportTicket, *filters)

    def open_ticket(self, summary, description, regarding=None):
        """

        """
        params = {
            "summary": summary,
            "description": description,
        }

        if regarding:
            if isinstance(regarding, Linode):
                params['linode_id'] = regarding.id
            elif isinstance(regarding, Domain):
                params['domain_id'] = regarding.id
            elif isinstance(regarding, NodeBalancer):
                params['nodebalancer_id'] = regarding.id
            elif isinstance(regarding, Volume):
                params['volume_id'] = regarding.id
            else:
                raise ValueError('Cannot open ticket regarding type {}!'.format(type(regarding)))


        result = self.client.post('/support/tickets', data=params)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when creating ticket!',
                    json=result)

        t = SupportTicket(self.client, result['id'], result)
        return t

class LinodeClient:
    def __init__(self, token, base_url="https://api.linode.com/v4", user_agent=None):
        self.base_url = base_url
        self._add_user_agent = user_agent
        self.token = token
        self.linode = LinodeGroup(self)
        self.profile = ProfileGroup(self)
        self.account = AccountGroup(self)
        self.networking = NetworkingGroup(self)
        self.support = SupportGroup(self)
        self.longview = LongviewGroup(self)

    @property
    def _user_agent(self):
        return '{}python-linode-api/{} {}'.format(
                '{} '.format(self._add_user_agent) if self._add_user_agent else '',
                package_version,
                requests.utils.default_user_agent()
        )

    def load(self, target_type, target_id, target_parent_id=None):
        """
        Constructs and immediately loads the object, circumventing the lazy-loading
        scheme by immediately making an api request.  Does not load related
        objects.  Raises an ApiError if the object cannot be loaded.
        """
        result = target_type.make_instance(target_id, self, parent_id=target_parent_id)
        result._api_get()

        return result

    def _api_call(self, endpoint, model=None, method=None, data=None, filters=None):
        """
        Makes a call to the linode api.  Data should only be given if the method is
        POST or PUT, and should be a dictionary
        """
        if not self.token:
            raise RuntimeError("You do not have an API token!")

        if not method:
            raise ValueError("Method is required for API calls!")

        if model:
            endpoint = endpoint.format(**vars(model))
        url = '{}{}'.format(self.base_url, endpoint)
        headers = {
            'Authorization': "Bearer {}".format(self.token),
            'Content-Type': 'application/json',
            'User-Agent': self._user_agent,
        }

        if filters:
            headers['X-Filter'] = json.dumps(filters)

        body = None
        if data is not None:
            body = json.dumps(data)

        response = method(url, headers=headers, data=body)

        warning = response.headers.get('Warning', None)
        if warning:
            logger.warning('Received warning from server: {}'.format(warning))

        if 399 < response.status_code < 600:
            j = None
            error_msg = '{}: '.format(response.status_code)
            try:
                j = response.json()
                if 'errors' in j.keys():
                    for e in j['errors']:
                        error_msg += '{}; '.format(e['reason']) \
                                if 'reason' in e.keys() else ''
            except:
                pass
            raise ApiError(error_msg, status=response.status_code, json=j)

        if response.status_code != 204:
            j = response.json()
        else:
            j = None # handle no response body

        return j

    def _get_objects(self, endpoint, cls, model=None, parent_id=None, filters=None):
        response_json = self.get(endpoint, model=model, filters=filters)

        if not "data" in response_json:
            raise UnexpectedResponseError("Problem with response!", json=response_json)

        if 'pages' in response_json:
            formatted_endpoint = endpoint
            if model:
                formatted_endpoint = formatted_endpoint.format(**vars(model))
            return PaginatedList.make_paginated_list(response_json, self, cls,
                    parent_id=parent_id, page_url=formatted_endpoint[1:],
                    filters=filters)
        return PaginatedList.make_list(response_json["data"], self, cls,
                parent_id=parent_id)

    def get(self, *args, **kwargs):
        return self._api_call(*args, method=requests.get, **kwargs)

    def post(self, *args, **kwargs):
        return self._api_call(*args, method=requests.post, **kwargs)

    def put(self, *args, **kwargs):
        return self._api_call(*args, method=requests.put, **kwargs)

    def delete(self, *args, **kwargs):
        return self._api_call(*args, method=requests.delete, **kwargs)

    # ungrouped list functions
    def get_regions(self, *filters):
        return self._get_and_filter(Region, *filters)

    def get_profile(self):
        """
        Returns this token's user's profile.  This is not a listing endpoint.
        """
        result = self.get('/profile')

        if not 'username' in result:
            raise UnexpectedResponseError('Unexpected response when getting profile!', json=result)

        p = Profile(self, result['username'], result)
        return p

    def get_account(self):
        """
        Returns account billing information
        """
        result = self.get('/account')

        if not 'email' in result:
            raise UnexpectedResponseError('Unexpected response when getting account!', json=result)

        return Account(self, result['email'], result)

    def get_images(self, *filters):
        return self._get_and_filter(Image, *filters)

    def create_image(self, disk, label=None, description=None):
        """
        Creates a new Image from a disk you own.
        """
        params = {
            "disk_id": disk.id if issubclass(type(disk), Base) else disk,
        }

        if label is not None:
            params["label"] = label

        if description is not None:
            params["description"] = description

        result = self.post('/images', data=params)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when creating an '
                                          'Image from disk {}'.format(disk))

        return Image(self, result['id'], result)

    def get_domains(self, *filters):
        return self._get_and_filter(Domain, *filters)

    def get_nodebalancers(self, *filters):
        return self._get_and_filter(NodeBalancer, *filters)

    def create_nodebalancer(self, region, **kwargs):
        params = {
            "region": region.id if isinstance(region, Base) else region,
        }
        params.update(kwargs)

        result = self.post('/nodebalancers', data=params)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when creating Nodebalaner!', json=result)

        n = NodeBalancer(self, result['id'], result)
        return n

    def create_domain(self, domain, master=True, **kwargs):
        params = {
            'domain': domain,
            'type': 'master' if master else 'slave',
        }
        params.update(kwargs)

        result = self.post('/domains', data=params)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when creating Domain!', json=result)

        d = Domain(self, result['id'], result)
        return d

    def get_volumes(self, *filters):
        return self._get_and_filter(Volume, *filters)

    def create_volume(self, label, region=None, linode=None, size=20, **kwargs):
        """
        Creates a new Block Storage Volume, either in the given region, or attached
        to the given linode.
        """
        if not (region or linode):
            raise ValueError('region or linode required!')

        params = {
            "label": label,
            "size": size,
            "region": region.id if issubclass(type(region), Base) else region,
            "linode_id": linode.id if issubclass(type(linode), Base) else linode,
        }
        params.update(kwargs)

        result = self.post('/volumes', data=params)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when creating volume!', json=result)

        v = Volume(self, result['id'], result)
        return v

    # helper functions
    def _filter_list(self, results, **filter_by):
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

    def _get_and_filter(self, obj_type, *filters):
        parsed_filters = None
        if filters:
            if(len(filters) > 1):
                parsed_filters = and_(*filters).dct # pylint: disable=no-value-for-parameter
            else:
                parsed_filters = filters[0].dct

        return self._get_objects(obj_type.api_list(), obj_type, filters=parsed_filters)

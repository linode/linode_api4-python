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
    """
    Encapsulates Linode-related methods of the :any:`LinodeClient`.  This
    should not be instantiated on its own, but should instead be used through
    an instance of :any:`LinodeClient`::

       client = LinodeClient(token)
       linodes = client.linode.get_instances() # use the LinodeGroup

    This group contains all features beneath the `/linode` group in the API v4.
    """
    def get_types(self, *filters):
        """
        Returns a list of Linode types.  These may be used to create or resize
        Linodes, or simply referenced on their own.  Types can be filtered to
        return specific types, for example::

           standard_types = client.linode.get_types(Type.class == "standard")

        :param filters: Any number of filters to apply to the query.

        :returns: A list of types that match the query.
        :rtype: PaginatedList of Type
        """
        return self.client._get_and_filter(Type, *filters)

    def get_instances(self, *filters):
        """
        Returns a list of Linodes on your account.  You may filter this query
        to return only Linodes that match specific criteria::

           prod_linodes = client.linode.get_instances(Linode.group == "prod")

        :param filters: Any number of filters to apply to this query.

        :returns: A list of Linodes that matched the query.
        :rtype: PaginatedList of Linode
        """
        return self.client._get_and_filter(Linode, *filters)

    def get_stackscripts(self, *filters, **kwargs):
        """
        Returns a list of :any:`StackScripts<StackScript>`, both public and
        private.  You may filter this query to return only
        :any:`StackScripts<StackScript>` that match certain criteria.  You may
        also request only your own private :any:`StackScripts<StackScript>`::

           my_stackscripts = client.linode.get_stackscripts(mine_only=True)

        :param filters: Any number of filters to apply to this query.
        :param mine_only: If True, returns only private StackScripts
        :type mine_only: bool

        :returns: A list of StackScripts matching the query.
        :rtype: PaginatedList of StackScript
        """
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
        """
        Returns a list of available :any:`Kernels<Kernel>`.  Kernels are used
        when creating or updating :any:`LinodeConfigs,LinodeConfig>`.

        :param filters: Any number of filters to apply to this query.

        :returns: A list of available kernels that match the query.
        :rtype: PaginatedList of Kernel
        """
        return self.client._get_and_filter(Kernel, *filters)

    # create things
    def create_instance(self, ltype, region, image=None,
            authorized_keys=None, **kwargs):
        """
        Creates a new Linode. This function has several modes of operation:

        **Create a Linode from an Image**

        To create a Linode from an :any:`Image`, call `create_instance` with
        a :any:`Type`, a :any:`Region`, and an :any:`Image`.  All three of
        these fields may be provided as either the ID or the appropriate object.
        In this mode, a root password will be generated and returned with the
        new Linode object.  For example::

           new_linode, password = client.linode.create_instance(
               "g5-standard-1",
               "us-east",
               image="linode/debian9")

           ltype = client.linode.get_types().first()
           region = client.get_regions().first()
           image = client.get_images().first()

           another_linode, password = client.linode.create_instance(
               ltype,
               region,
               image=image)

        **Create a Linode from StackScript**

        When creating a Linode from a :any:`StackScript`, an :any:`Image` that
        the StackScript support must be provided..  You must also provide any
        required StackScript data for the script's User Defined Fields..  For
        example, if deploying `StackScript 10079`_ (which deploys a new Linode
        with a user created from keys on `github`_::

           stackscript = StackScript(client, 10079)

           new_linode, password = client.linode.create_instance(
              "g5-standard-2",
              "us-east",
              image="linode/debian9",
              stackscript=stackscript,
              stackscript_data={"gh_username": "example"})

        In the above example, "gh_username" is the name of a User Defined Field
        in the chosen StackScript.  For more information on StackScripts, see
        the `StackScript guide`_.

        .. _`StackScript 10079`: https://www.linode.com/stackscripts/view/10079
        .. _`github`: https://github.com
        .. _`StackScript guide`: https://www.linode.com/docs/platform/stackscripts/

        **Create a Linode from a Backup**

        To create a new Linode by restoring a :any:`Backup` to it, provide a
        :any:`Type`, a :any:`Region`, and the :any:`Backup` to restore.  You
        may provide either IDs or objects for all of these fields::

           existing_linode = Linode(client, 123)
           snapshot = existing_linode.available_backups.snapshot.current

           new_linode = client.linode.create_instance(
               "g5-standard-1",
               "us-east",
               backup=snapshot)

        **Create an empty Linode**

        If you want to create an empty Linode that you will configure manually,
        simply call `create_instance` with a :any:`Type` and a :any:`Region`::

           empty_linode = client.linode.create_instance("g5-standard-2", "us-east")

        When created this way, the Linode will not be booted and cannot boot
        successfully until disks and configs are created, or it is otherwise
        configured.

        :param ltype: The Linode Type we are creating
        :type ltype: str or LinodeType
        :param region: The Region in which we are creating the Linode
        :type region: str or Region
        :param image: The Image to deploy to this Linode.  If this is provided
                      and no root_pass is given, a password will be generated
                      and returned along with the new Linode.
        :type image: str or Image
        :param stackscript: The StackScript to deploy to the new Linode.  If
                            provided, "image" is required and must be compatible
                            with the chosen StackScript.
        :type stackscript: int or StackScript
        :param stackscript_data: Values for the User Defined Fields defined in
                                 the chosen StackScript.  Does nothing if
                                 StackScript is not provided.
        :type stackscript_data: dict
        :param backup: The Backup to restore to the new Linode.  May not be
                       provided if "image" is given.
        :type backup: int of Backup
        :param authorized_keys: The ssh public keys to install in the linode's
                                /root/.ssh/authorized_keys file.  Each entry may
                                be a single key, or a path to a file containing
                                the key.
        :type authorized_keys: list or str
        :param label: The display label for the new Linode
        :type label: str
        :param group: The display group for the new Linode
        :type group: str
        :param booted: Whether the new Linode should be booted.  This will
                       default to True if the Linode is deployed from an Image
                       or Backup.
        :type booted: bool

        :returns: A new Linode object, or a tuple containing the new Linode and
                  the generated password.
        :rtype: Linode or tuple(Linode, str)
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

        if "stackscript" in kwargs:
            # translate stackscripts
            kwargs["stackscript_id"] = (kwargs["stackscript"].id if issubclass(type(kwargs["stackscript"]), Base)
                                        else kwargs["stackscript"])
            del kwargs["stackscript"]

        if "backup" in kwargs:
            # translate backups
            kwargs["backup_id"] = (kwargs["backup"].id if issubclass(type(kwargs["backup"]), Base)
                                   else kwargs["backup"])
            del kwargs["backup"]

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
        """
        Creates a new :any:`StackScript` on your account.

        :param label: The label for this StackScript.
        :type label: str
        :param script: The script to run when a :any:`Linode` is deployed with
                       this StackScript.  Must begin with a shebang (#!).
        :type script: str
        :param images: A list of :any:`Images<Image>` that this StackScript
                       supports.  Linodes will not be deployed from this
                       StackScript unless deployed from one of these Images.
        :type images: list of Image
        :param desc: A description for this StackScript.
        :type desc: str
        :param public: Whether this StackScript is public.  Defaults to False.
                       Once a StackScript is made public, it may not be set
                       back to private.
        :type public: bool

        :returns: The new StackScript
        :rtype: StackScript
        """
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
            "images": image_list,
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

def create_user(self, email, username, restricted=True):
    """
    Creates a new user on your account.  If you create an unrestricted user,
    they will immediately be able to access everything on your account.  If
    you create a restricted user, you must grant them access to parts of your
    account that you want to allow them to manage (see :any:`User.grants` for
    details).

    The new user will receive an email inviting them to set up their password.
    This must be completed before they can log in.

    :param email: The new user's email address.  This is used to finish setting
                  up their user account.
    :type email: str
    :param username: The new user's unique username.  They will use this username
                     to log in.
    :type username: str
    :param restricted: If True, the new user must be granted access to parts of
                       the account before they can do anything.  If False, the
                       new user will immediately be able to manage the entire
                       account.  Defaults to True.
    :type restricted: True

    :returns The new User.
    :rtype: User
    """
    params = {
        "email": email,
        "username": username,
        "restricted": restricted,
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
        Redistributes :any:`IP Addressees<IPAddress>` within a single region.
        This function takes a :any:`Region` and a list of assignments to make,
        then requests that the assignments take place.  If any :any:`Linode`
        ends up without a public IP, or with more than one private IP, all of
        the assignments will fail.

        Example usage::

           linode1 = Linode(client, 123)
           linode2 = Linode(client, 456)

           # swap IPs between linodes 1 and 2
           client.networking.assign_ips(linode1.region,
                                        linode1.ips.ipv4.public[0].to(linode2),
                                        linode2.ips.ipv4.public[0].to(linode1))

        :param region: The Region in which the assignments should take place.
                       All Linodes and IPAddresses involved in the assignment
                       must be within this region.
        :type region: str or Region
        :param assignments: Any number of assignments to make.  See
                            :any:`IPAddress.to` for details on how to construct
                            assignments.
        :type assignments: dct
        """
        for a in assignments:
            if not 'address' in a or not 'linode_id' in a:
                raise ValueError("Invalid assignment: {}".format(a))
        if isinstance(region, Region):
            region = region.id

        self.client.post('/networking/ipv4/assign', data={
            "region": region,
            "assignments": [ a for a in assignments ],
        })

    def allocate_ip(self, linode, public=True):
        """
        Allocates an IP to a Linode you own.  Additional IPs must be requested
        by opening a support ticket first.

        :param linode: The Linode to allocate the new IP for.
        :type linode: Linode or int
        :param public: If True, allocate a public IP address.  Defaults to True.
        :type public: bool

        :returns: The new IPAddress
        :rtype: IPAddress
        """
        result = self.client.post('/networking/ipv4/', data={
            "linode_id": linode.id if isinstance(linode, Base) else linode,
            "type": "ipv4",
            "public": public,
        })

        if not 'address' in result:
            raise UnexpectedResponseError('Unexpected response when adding IPv4 address!',
                    json=result)

        ip = IPAddress(self.client, result['address'], result)
        return ip

    def set_shared_ips(self, linode, *ips):
        """
        Shares the given list of :any:`IPAddresses<IPAddress>` with the provided
        :any:`Linode`.  This will enable the provided Linode to bring up the
        shared IP Addresses even though it does not own them.

        :param linode: The Linode to share the IPAddresses with.  This Linode
                       will be able to bring up the given addresses.
        :type: linode: int or Linode
        :param ips: Any number of IPAddresses to share to the Linode.
        :type ips: str or IPAddress
        """
        if not isinstance(linode, Linode):
            # make this an object
            linode = Linode(self.client, linode)

        params = []
        for ip in ips:
            if isinstance(ip, str):
                params.append(ip)
            elif isinstance(ip, IPAddress):
                params.append(ip.address)
            else:
                params.append(str(ip)) # and hope that works

        params = {
            "ips": params
        }

        self.client.post('{}/networking/ipv4/share'.format(Linode.api_endpoint),
                         model=linode, data=params)

        linode.invalidate() # clear the Linode's shared IPs

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
        """
        The main interface to the Linode API.

        :param token: The authentication token to use for communication with the
                      API.  Can be either a Personal Access Token or an OAuth Token.
        :type token: str
        :param base_url: The base URL for API requests.  Generally, you shouldn't
                         change this.
        :type base_url: str
        :param user_agent: What to append to the User Agent of all requests made
                           by this client.  Setting this allows Linode's internal
                           monitoring applications to track the usage of your
                           application.  Setting this is not necessary, but some
                           applications may desire this behavior.
        :type user_agent: str
        """
        self.base_url = base_url
        self._add_user_agent = user_agent
        self.token = token

        #: Access methods related to Linodes - see :any:`LinodeGroup` for
        #: more information
        self.linode = LinodeGroup(self)

        #: Access methods related to your user - see :any:`ProfileGroup` for
        #: more information
        self.profile = ProfileGroup(self)

        #: Access methods related to your account - see :any:`AccountGroup` for
        #: more information
        self.account = AccountGroup(self)

        #: Access methods related to networking on your account - see
        #: :any:`NetworkingGroup` for more information
        self.networking = NetworkingGroup(self)

        #: Access methods related to support - see :any:`SupportGroup` for more
        #: information
        self.support = SupportGroup(self)

        #: Access information related to the Longview service - see
        #: :any:`LongviewGroup` for more information
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
        Constructs and immediately loads the object, circumventing the
        lazy-loading scheme by immediately making an API request.  Does not
        load related objects.

        For example, if you wanted to load a :any:`Linode` object with ID 123,
        you could do this::

           loaded_linode = client.load(Linode, 123)

        Similarly, if you instead wanted to load a :any:`NodeBalancerConfig`,
        you could do so like this::

           loaded_nodebalancer_config = client.load(NodeBalancerConfig, 456, 432)

        :param target_type: The type of object to create.
        :type target_type: type
        :param target_id: The ID of the object to create.
        :type target_id: int or str
        :param target_parent_id: The parent ID of the object to create, if
                                 applicable.
        :type target_parent_id: int, str, or None

        :returns: The resulting object, fully loaded.
        :rtype: target_type
        :raise ApiError: if the requested object could not be loaded.
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
        """
        Returns the available Regions for Linode products.

        :param filters: Any number of filters to apply to the query.

        :returns: A list of available Regions.
        :rtype: PaginatedList of Region
        """
        return self._get_and_filter(Region, *filters)

    def get_profile(self):
        """
        Retrieve the acting user's Profile, containing information about the
        current user such as their email address, username, and uid.

        :returns: The acting user's profile.
        :rtype: Profile
        """
        result = self.get('/profile')

        if not 'username' in result:
            raise UnexpectedResponseError('Unexpected response when getting profile!', json=result)

        p = Profile(self, result['username'], result)
        return p

    def get_account(self):
        """
        Retrieves information about the acting user's account, such as billing
        information.

        :returns: Returns the acting user's account information.
        :rtype: Account
        """
        result = self.get('/account')

        if not 'email' in result:
            raise UnexpectedResponseError('Unexpected response when getting account!', json=result)

        return Account(self, result['email'], result)

    def get_images(self, *filters):
        """
        Retrieves a list of available Images, including public and private
        Images available to the acting user.  You can filter this query to
        retrieve only Images relevant to a specific query, for example::

           debian_images = client.get_images(
               Image.vendor == "debain")

        :param filters: Any number of filters to apply to the query.

        :returns: A list of available Images.
        :rtype: PaginatedList of Image
        """
        return self._get_and_filter(Image, *filters)

    def create_image(self, disk, label=None, description=None):
        """
        Creates a new Image from a disk you own.

        :param disk: The Disk to imagize.
        :type disk: Disk or int
        :param label: The label for the resulting Image (defaults to the disk's
                      label.
        :type label: str
        :param description: The description for the new Image.
        :type description: str

        :returns: The new Image.
        :rtype: Image
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
        """
        Retrieves all of the Domains the acting user has access to.

        :param filters: Any number of filters to apply to this query.

        :returns: A list of Domains the acting user can access.
        :rtype: PaginatedList of Domain
        """
        return self._get_and_filter(Domain, *filters)

    def get_nodebalancers(self, *filters):
        """
        Retrieves all of the NodeBalancers the acting user has access to.

        :param filters: Any number of filters to apply to this query.

        :returns: A list of NodeBalancers the acting user can access.
        :rtype: PaginatedList of NodeBalancers
        """
        return self._get_and_filter(NodeBalancer, *filters)

    def create_nodebalancer(self, region, **kwargs):
        """
        Creates a new NodeBalancer in the given Region.

        :param region: The Region in which to create the NodeBalancer.
        :type region: Region or str

        :returns: The new NodeBalancer
        :rtype: NodeBalancer
        """
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
        """
        Registers a new Domain on the acting user's account.  Make sure to point
        your registrar to Linode's nameservers so that Linode's DNS manager will
        correctly serve your domain.

        :param domain: The domain to register to Linode's DNS manager.
        :type domain: str
        :param master: Whether this is a master (defaults to true)
        :type master: bool

        :returns: The new Domain object.
        :rtype: Domain
        """
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
        """
        Retrieves the Block Storage Volumes your user has access to.

        :param filters: Any number of filters to apply to this query.

        :returns: A list of Volumes the acting user can access.
        :rtype: PaginatedList of Volume
        """
        return self._get_and_filter(Volume, *filters)

    def create_volume(self, label, region=None, linode=None, size=20, **kwargs):
        """
        Creates a new Block Storage Volume, either in the given Region or
        attached to the given Linode.

        :param label: The label for the new Volume.
        :type label: str
        :param region: The Region to create this Volume in.  Not required if
                       `linode` is provided.
        :type region: Region or str
        :param linode: The Linode to attach this Volume to.  If not given, the
                       new Volume will not be attached to anything.
        :type linode: Linode or int
        :param size: The size, in GB, of the new Volume.  Defaults to 20.
        :type size: int

        :returns: The new Volume.
        :rtype: Volume
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

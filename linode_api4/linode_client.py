import json
import logging
from datetime import datetime
import os

import pkg_resources
import requests

from linode_api4.errors import ApiError, UnexpectedResponseError
from linode_api4.objects import *
from linode_api4.objects.filtering import Filter

from .common import load_and_validate_keys, SSH_KEY_TYPES
from .paginated_list import PaginatedList

package_version = pkg_resources.require("linode_api4")[0].version

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
       instances = client.linode.instances() # use the LinodeGroup

    This group contains all features beneath the `/linode` group in the API v4.
    """
    def types(self, *filters):
        """
        Returns a list of Linode Instance types.  These may be used to create
        or resize Linodes, or simply referenced on their own.  Types can be
        filtered to return specific types, for example::

           standard_types = client.linode.types(Type.class == "standard")

        :param filters: Any number of filters to apply to the query.

        :returns: A list of types that match the query.
        :rtype: PaginatedList of Type
        """
        return self.client._get_and_filter(Type, *filters)

    def instances(self, *filters):
        """
        Returns a list of Linode Instances on your account.  You may filter
        this query to return only Linodes that match specific criteria::

           prod_linodes = client.linode.instances(Instance.group == "prod")

        :param filters: Any number of filters to apply to this query.

        :returns: A list of Instances that matched the query.
        :rtype: PaginatedList of Instance
        """
        return self.client._get_and_filter(Instance, *filters)

    def stackscripts(self, *filters, **kwargs):
        """
        Returns a list of :any:`StackScripts<StackScript>`, both public and
        private.  You may filter this query to return only
        :any:`StackScripts<StackScript>` that match certain criteria.  You may
        also request only your own private :any:`StackScripts<StackScript>`::

           my_stackscripts = client.linode.stackscripts(mine_only=True)

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
                    filters = list(filters)
                    filters[0] = filters[0] & new_filter
                else:
                    filters = [new_filter]

            del kwargs['mine_only']

        if kwargs:
            raise TypeError("stackscripts() got unexpected keyword argument '{}'".format(kwargs.popitem()[0]))

        return self.client._get_and_filter(StackScript, *filters)

    def kernels(self, *filters):
        """
        Returns a list of available :any:`Kernels<Kernel>`.  Kernels are used
        when creating or updating :any:`LinodeConfigs,LinodeConfig>`.

        :param filters: Any number of filters to apply to this query.

        :returns: A list of available kernels that match the query.
        :rtype: PaginatedList of Kernel
        """
        return self.client._get_and_filter(Kernel, *filters)

    # create things
    def instance_create(self, ltype, region, image=None,
            authorized_keys=None, **kwargs):
        """
        Creates a new Linode Instance. This function has several modes of operation:

        **Create an Instance from an Image**

        To create an Instance from an :any:`Image`, call `instance_create` with
        a :any:`Type`, a :any:`Region`, and an :any:`Image`.  All three of
        these fields may be provided as either the ID or the appropriate object.
        In this mode, a root password will be generated and returned with the
        new Instance object.  For example::

           new_linode, password = client.linode.instance_create(
               "g6-standard-2",
               "us-east",
               image="linode/debian9")

           ltype = client.linode.types().first()
           region = client.regions().first()
           image = client.images().first()

           another_linode, password = client.linode.instance_create(
               ltype,
               region,
               image=image)

        **Create an Instance from StackScript**

        When creating an Instance from a :any:`StackScript`, an :any:`Image` that
        the StackScript support must be provided..  You must also provide any
        required StackScript data for the script's User Defined Fields..  For
        example, if deploying `StackScript 10079`_ (which deploys a new Instance
        with a user created from keys on `github`_::

           stackscript = StackScript(client, 10079)

           new_linode, password = client.linode.instance_create(
              "g6-standard-2",
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

        **Create an Instance from a Backup**

        To create a new Instance by restoring a :any:`Backup` to it, provide a
        :any:`Type`, a :any:`Region`, and the :any:`Backup` to restore.  You
        may provide either IDs or objects for all of these fields::

           existing_linode = Instance(client, 123)
           snapshot = existing_linode.available_backups.snapshot.current

           new_linode = client.linode.instance_create(
               "g6-standard-2",
               "us-east",
               backup=snapshot)

        **Create an empty Instance**

        If you want to create an empty Instance that you will configure manually,
        simply call `instance_create` with a :any:`Type` and a :any:`Region`::

           empty_linode = client.linode.instance_create("g6-standard-2", "us-east")

        When created this way, the Instance will not be booted and cannot boot
        successfully until disks and configs are created, or it is otherwise
        configured.

        :param ltype: The Instance Type we are creating
        :type ltype: str or Type
        :param region: The Region in which we are creating the Instance
        :type region: str or Region
        :param image: The Image to deploy to this Instance. If this is provided
                      and no root_pass is given, a password will be generated
                      and returned along with the new Instance.
        :type image: str or Image
        :param stackscript: The StackScript to deploy to the new Instance.  If
                            provided, "image" is required and must be compatible
                            with the chosen StackScript.
        :type stackscript: int or StackScript
        :param stackscript_data: Values for the User Defined Fields defined in
                                 the chosen StackScript.  Does nothing if
                                 StackScript is not provided.
        :type stackscript_data: dict
        :param backup: The Backup to restore to the new Instance.  May not be
                       provided if "image" is given.
        :type backup: int of Backup
        :param authorized_keys: The ssh public keys to install in the linode's
                                /root/.ssh/authorized_keys file.  Each entry may
                                be a single key, or a path to a file containing
                                the key.
        :type authorized_keys: list or str
        :param label: The display label for the new Instance
        :type label: str
        :param group: The display group for the new Instance
        :type group: str
        :param booted: Whether the new Instance should be booted.  This will
                       default to True if the Instance is deployed from an Image
                       or Backup.
        :type booted: bool

        :returns: A new Instance object, or a tuple containing the new Instance and
                  the generated password.
        :rtype: Instance or tuple(Instance, str)
        :raises ApiError: If contacting the API fails
        :raises UnexpectedResponseError: If the API resposne is somehow malformed.
                                         This usually indicates that you are using
                                         an outdated library.
        """
        ret_pass = None
        if image and not 'root_pass' in kwargs:
            ret_pass = Instance.generate_root_password()
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

        l = Instance(self.client, result['id'], result)
        if not ret_pass:
            return l
        return l, ret_pass

    def stackscript_create(self, label, script, images, desc=None, public=False, **kwargs):
        """
        Creates a new :any:`StackScript` on your account.

        :param label: The label for this StackScript.
        :type label: str
        :param script: The script to run when an :any:`Instance` is deployed with
                       this StackScript.  Must begin with a shebang (#!).
        :type script: str
        :param images: A list of :any:`Images<Image>` that this StackScript
                       supports.  Instances will not be deployed from this
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
    def __call__(self):
        """
        Retrieve the acting user's Profile, containing information about the
        current user such as their email address, username, and uid.  This is
        intended to be called off of a :any:`LinodeClient` object, like this::

           profile = client.profile()

        :returns: The acting user's profile.
        :rtype: Profile
        """
        result = self.client.get('/profile')

        if not 'username' in result:
            raise UnexpectedResponseError('Unexpected response when getting profile!', json=result)

        p = Profile(self.client, result['username'], result)
        return p

    def tokens(self, *filters):
        """
        Returns the Person Access Tokens active for this user
        """
        return self.client._get_and_filter(PersonalAccessToken, *filters)

    def token_create(self, label=None, expiry=None, scopes=None, **kwargs):
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

        result = self.client.post('/profile/tokens', data=kwargs)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when creating Personal Access '
                    'Token!', json=result)

        token = PersonalAccessToken(self.client, result['id'], result)
        return token

    def apps(self, *filters):
        """
        Returns the Authorized Applications for this user
        """
        return self.client._get_and_filter(AuthorizedApp, *filters)

    def ssh_keys(self, *filters):
        """
        Returns the SSH Public Keys uploaded to your profile
        """
        return self.client._get_and_filter(SSHKey, *filters)

    def ssh_key_upload(self, key, label):
        """
        Uploads a new SSH Public Key to your profile  This key can be used in
        later Linode deployments.

        :param key: The ssh key, or a path to the ssh key.  If a path is provided,
                    the file at the path must exist and be readable or an exception
                    will be thrown.
        :type key: str
        :param label: The name to give this key.  This is purely aesthetic.
        :type label: str

        :returns: The newly uploaded SSH Key
        :rtype: SSHKey
        :raises ValueError: If the key provided does not appear to be valid, and
                            does not appear to be a path to a valid key.
        """
        if not key.startswith(SSH_KEY_TYPES):
            # this might be a file path - look for it
            path = os.path.expanduser(key)
            if os.path.isfile(path):
                with open(path) as f:
                    key = f.read().strip()
            if not key.startswith(SSH_KEY_TYPES):
                raise ValueError('Invalid SSH Public Key')

        params = {
            'ssh_key': key,
            'label': label,
        }

        result = self.client.post('/profile/sshkeys', data=params)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when uploading SSH Key!',
                                          json=result)

        ssh_key = SSHKey(self.client, result['id'], result)
        return ssh_key


class LKEGroup(Group):
    """
    Encapsulates LKE-related methods of the :any:`LinodeClient`.  This
    should not be instantiated on its own, but should instead be used through
    an instance of :any:`LinodeClient`::

       client = LinodeClient(token)
       instances = client.lke.clusters() # use the LKEGroup

    This group contains all features beneath the `/lke` group in the API v4.
    """
    def versions(self, *filters):
        """
        Returns a :any:`PaginatedList` of :any:`KubeVersion` objects that can be
        used when creating an LKE Cluster.

        :param filters: Any number of filters to apply to the query.

        :returns: A Paginated List of kube versions that match the query.
        :rtype: PaginatedList of KubeVersion
        """
        return self.client._get_and_filter(KubeVersion, *filters)

    def clusters(self, *filters):
        """
        Returns a :any:`PaginagtedList` of :any:`LKECluster` objects that belong
        to this account.

        :param filters: Any number of filters to apply to the query.

        :returns: A Paginated List of LKE clusters that match the query.
        :rtype: PaginatedList of LKECluster
        """
        return self.client._get_and_filter(LKECluster, *filters)

    def cluster_create(self, region, label, node_pools, **kwargs):
        """
        Creates an :any:`LKECluster` on this account in the given region, with
        the given label, and with node pools as described.  For example::

           client = LinodeClient(TOKEN)

           # look up Region and Types to use.  In this example I'm just using
           # the first ones returned.
           target_region = client.regions().first()
           node_type = client.linode.types()[0]
           node_type_2 = client.linode.types()[1]

           new_cluster = client.lke.cluster_create(
               target_region,
               "example-cluster",
               [client.lke.node_pool(node_type, 3), client.lke.node_pool(node_type_2, 3)]
            )

        :param region: The Region to create this LKE Cluster in.
        :type region: Region of str
        :param label: The label for the new LKE Cluster.
        :type label: str
        :param node_pools: The Node Pools to create.
        :type node_pools: one or a list of dicts containing keys "type" and "count".  See
                          :any:`node_pool` for a convenient way to create correctly-
                          formatted dicts.
        :param kwargs: Any other arguments to pass along to the API.  See the API
                       docs for possible values.

        :returns: The new LKE Cluster
        :rtype: LKECluster
        """
        pools = []
        if not isinstance(node_pools, list):
            node_pools = [node_pools]

        for c in node_pools:
            if isinstance(c, dict):
                new_pool = {
                    "type": c["type"].id if "type" in c and issubclass(c["type"], Base) else c.get("type"),
                    "count": c.get("count"),
                }

                pools += [new_pool]

        params = {
            "label": label,
            "region": region.id if issubclass(region, Base) else region,
            "node_pools": pools,
        }
        params.update(kwargs)

        result = self.client.post('/lke/clusters', data=params)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when creating LKE cluster!', json=result)

        return LKECluster(self.client, result['id'], result)

    def node_pool(self, node_type, node_count):
        """
        Returns a dict that is suitable for passing into the `node_pools` array
        of :any:`cluster_create`.  This is a convenience method, and need not be
        used to create Node Pools.  For proper usage, see the docs for :any:`cluster_create`.

        :param node_type: The type of node to create in this node pool.
        :type node_type: Type or str
        :param node_count: The number of nodes to create in this node pool.
        :type node_count: int

        :returns: A dict describing the desired node pool.
        :rtype: dict
        """
        return {
            "type": node_type,
            "count": node_count,
        }

class LongviewGroup(Group):
    def clients(self, *filters):
        """
        Requests and returns a paginated list of LongviewClients on your
        account.
        """
        return self.client._get_and_filter(LongviewClient, *filters)

    def client_create(self, label=None):
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

    def subscriptions(self, *filters):
        """
        Requests and returns a paginated list of LongviewSubscriptions available
        """
        return self.client._get_and_filter(LongviewSubscription, *filters)


class AccountGroup(Group):
    def __call__(self):
        """
        Retrieves information about the acting user's account, such as billing
        information.  This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           account = client.account()

        :returns: Returns the acting user's account information.
        :rtype: Account
        """
        result = self.client.get('/account')

        if not 'email' in result:
            raise UnexpectedResponseError('Unexpected response when getting account!', json=result)

        return Account(self.client, result['email'], result)


    def events(self, *filters):
        return self.client._get_and_filter(Event, *filters)

    def events_mark_seen(self, event):
        """
        Marks event as the last event we have seen.  If event is an int, it is treated
        as an event_id, otherwise it should be an event object whose id will be used.
        """
        last_seen = event if isinstance(event, int) else event.id
        self.client.post('{}/seen'.format(Event.api_endpoint), model=Event(self.client, last_seen))

    def settings(self):
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

    def invoices(self):
        """
        Returns Invoices issued to this account
        """
        return self.client._get_and_filter(Invoice)

    def payments(self):
        """
        Returns a list of Payments made to this account
        """
        return self.client._get_and_filter(Payment)

    def oauth_clients(self, *filters):
        """
        Returns the OAuth Clients associated to this account
        """
        return self.client._get_and_filter(OAuthClient, *filters)

    def oauth_client_create(self, name, redirect_uri, **kwargs):
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

    def users(self, *filters):
        """
        Returns a list of users on this account
        """
        return self.client._get_and_filter(User, *filters)

    def transfer(self):
        """
        Returns a MappedObject containing the account's transfer pool data
        """
        result = self.client.get('/account/transfer')

        if not 'used' in result:
            raise UnexpectedResponseError('Unexpected response when getting Transfer Pool!')

        return MappedObject(**result)

    def user_create(self, email, username, restricted=True):
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
    def ips(self, *filters):
        return self.client._get_and_filter(IPAddress, *filters)

    def ipv6_ranges(self, *filters):
        return self.client._get_and_filter(IPv6Range, *filters)

    def ipv6_pools(self, *filters):
        return self.client._get_and_filter(IPv6Pool, *filters)

    def ips_assign(self, region, *assignments):
        """
        Redistributes :any:`IP Addressees<IPAddress>` within a single region.
        This function takes a :any:`Region` and a list of assignments to make,
        then requests that the assignments take place.  If any :any:`Instance`
        ends up without a public IP, or with more than one private IP, all of
        the assignments will fail.

        .. note::
           This function *does not* update the local Linode Instance objects
           when called.  In order to see the new addresses on the local
           instance objects, be sure to invalidate them with ``invalidate()``
           after this completes.

        Example usage::

           linode1 = Instance(client, 123)
           linode2 = Instance(client, 456)

           # swap IPs between linodes 1 and 2
           client.networking.assign_ips(linode1.region,
                                        linode1.ips.ipv4.public[0].to(linode2),
                                        linode2.ips.ipv4.public[0].to(linode1))

           # make sure linode1 and linode2 have updated ipv4 and ips values
           linode1.invalidate()
           linode2.invalidate()


        :param region: The Region in which the assignments should take place.
                       All Instances and IPAddresses involved in the assignment
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
            "assignments": assignments,
        })

    def ip_allocate(self, linode, public=True):
        """
        Allocates an IP to a Instance you own.  Additional IPs must be requested
        by opening a support ticket first.

        :param linode: The Instance to allocate the new IP for.
        :type linode: Instance or int
        :param public: If True, allocate a public IP address.  Defaults to True.
        :type public: bool

        :returns: The new IPAddress
        :rtype: IPAddress
        """
        result = self.client.post('/networking/ips/', data={
            "linode_id": linode.id if isinstance(linode, Base) else linode,
            "type": "ipv4",
            "public": public,
        })

        if not 'address' in result:
            raise UnexpectedResponseError('Unexpected response when adding IPv4 address!',
                    json=result)

        ip = IPAddress(self.client, result['address'], result)
        return ip

    def ips_share(self, linode, *ips):
        """
        Shares the given list of :any:`IPAddresses<IPAddress>` with the provided
        :any:`Instance`.  This will enable the provided Instance to bring up the
        shared IP Addresses even though it does not own them.

        :param linode: The Instance to share the IPAddresses with.  This Instance
                       will be able to bring up the given addresses.
        :type: linode: int or Instance
        :param ips: Any number of IPAddresses to share to the Instance.
        :type ips: str or IPAddress
        """
        if not isinstance(linode, Instance):
            # make this an object
            linode = Instance(self.client, linode)

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

        self.client.post('{}/networking/ipv4/share'.format(Instance.api_endpoint),
                         model=linode, data=params)

        linode.invalidate() # clear the Instance's shared IPs

class SupportGroup(Group):
    def tickets(self, *filters):
        return self.client._get_and_filter(SupportTicket, *filters)

    def ticket_open(self, summary, description, regarding=None):
        """

        """
        params = {
            "summary": summary,
            "description": description,
        }

        if regarding:
            if isinstance(regarding, Instance):
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


class ObjectStorageGroup(Group):
    """
    This group encapsulates all endpoints under /object-storage, including viewing
    available clusters and managing keys.
    """
    def clusters(self, *filters):
        """
        Returns a list of available Object Storage Clusters.  You may filter
        this query to return only Clusters that are available in a specific region::

           us_east_clusters = client.object_storage.clusters(ObjectStorageCluster.region == "us-east")

        :param filters: Any number of filters to apply to this query.

        :returns: A list of Object Storage Clusters that matched the query.
        :rtype: PaginatedList of ObjectStorageCluster
        """
        return self.client._get_and_filter(ObjectStorageCluster, *filters)

    def keys(self, *filters):
        """
        Returns a list of Object Storage Keys active on this account.  These keys
        allow third-party applications to interact directly with Linode Object Storage.

        :param filters: Any number of filters to apply to this query.

        :returns: A list of Object Storage Keys that matched the query.
        :rtype: PaginatedList of ObjectStorageKeys
        """
        return self.client._get_and_filter(ObjectStorageKeys, *filters)

    def keys_create(self, label, bucket_access=None):
        """
        Creates a new Object Storage keypair that may be used to interact directly
        with Linode Object Storage in third-party applications.  This response is
        the only time that "secret_key" will be populated - be sure to capture its
        value or it will be lost forever.

        If given, `bucket_access` will cause the new keys to be restricted to only
        the specified level of access for the specified buckets.  For example, to
        create a keypair that can only access the "example" bucket in all clusters
        (and assuming you own that bucket in every cluster), you might do this::

           client = LinodeClient(TOKEN)

           # look up clusters
           all_clusters = client.object_storage.clusters()

           new_keys = client.object_storage.keys_create(
               "restricted-keys",
               bucket_access=[
                   client.object_storage.bucket_access(cluster, "example", "read_write")
                   for cluster in all_clusters
               ],
           )

        To create a keypair that can only read from the bucket "example2" in the
        "us-east-1" cluster (an assuming you own that bucket in that cluster),
        you might do this::

           client = LinodeClient(TOKEN)
           new_keys_2 = client.object_storage.keys_create(
               "restricted-keys-2",
               bucket_access=client.object_storage.bucket_access("us-east-1", "example2", "read_only"),
           )

        :param label: The label for this keypair, for identification only.
        :type label: str
        :param bucket_access: One or a list of dicts with keys "cluster,"
                              "permissions", and "bucket_name".  If given, the
                              resulting Object Storage keys will only have the
                              requested level of access to the requested buckets,
                              if they exist and are owned by you.  See the provided
                              :any:`bucket_access` function for a convenient way
                              to create these dicts.
        :type bucket_access: dict or list of dict

        :returns: The new keypair, with the secret key populated.
        :rtype: ObjectStorageKeys
        """
        params = {
            "label": label
        }

        if bucket_access is not None:
            if not isinstance(bucket_access, list):
                bucket_access = [bucket_access]

            ba = [
                {
                    "permissions": c.get("permissions"),
                    "bucket_name": c.get("bucket_name"),
                    "cluster": c.id if "cluster" in c and issubclass(c["cluster"], Base) else c.get("cluster"),
                } for c in bucket_access
            ]

            params['bucket_access'] = ba

        result = self.client.post('/object-storage/keys', data=params)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when creating Object Storage Keys!', json=result)

        ret = ObjectStorageKeys(self.client, result['id'], result)
        return ret

    def bucket_access(self, cluster, bucket_name, permissions):
        """
        Returns a dict formatted to be included in the `bucket_access` argument
        of :any:`keys_create`.  See the docs for that method for an example of
        usage.

        :param cluster: The Object Storage cluster to grant access in.
        :type cluster: :any:`ObjectStorageCluster` or str
        :param bucket_name: The name of the bucket to grant access to.
        :type bucket_name: str
        :param permissions: The permissions to grant.  Should be one of "read_only"
                            or "read_write".
        :type permissions: str

        :returns: A dict formatted correctly for specifying  bucket access for
                  new keys.
        :rtype: dict
        """
        return {
            "cluster": cluster,
            "bucket_name": bucket_name,
            "permissions": permissions,
        }

    def cancel(self):
        """
        Cancels Object Storage service.  This may be a destructive operation.  Once
        cancelled, you will no longer receive the transfer for or be billed for
        Object Storage, and all keys will be invalidated.
        """
        self.client.post('/object-storage/cancel', data={})
        return True


class LinodeClient:
    def __init__(self, token, base_url="https://api.linode.com/v4", user_agent=None, page_size=None):
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
        :param page_size: The default size to request pages at.  If not given,
                                  the API's default page size is used.  Valid values
                                  can be found in the API docs, but at time of writing
                                  are between 25 and 500.
        :type page_size: int
        """
        self.base_url = base_url
        self._add_user_agent = user_agent
        self.token = token
        self.session = requests.Session()
        self.page_size = page_size

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

        #: Access methods related to Object Storage - see :any:`ObjectStorageGroup`
        #: for more information
        self.object_storage = ObjectStorageGroup(self)

        #: Access methods related to LKE - see :any:`LKEGroup` for more information.
        self.lke = LKEGroup(self)

    @property
    def _user_agent(self):
        return '{}python-linode_api4/{} {}'.format(
                '{} '.format(self._add_user_agent) if self._add_user_agent else '',
                package_version,
                requests.utils.default_user_agent()
        )

    def load(self, target_type, target_id, target_parent_id=None):
        """
        Constructs and immediately loads the object, circumventing the
        lazy-loading scheme by immediately making an API request.  Does not
        load related objects.

        For example, if you wanted to load an :any:`Instance` object with ID 123,
        you could do this::

           loaded_linode = client.load(Instance, 123)

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
        # handle non-default page sizes
        call_endpoint = endpoint
        if self.page_size is not None:
            call_endpoint += "?page_size={}".format(self.page_size)

        response_json = self.get(call_endpoint, model=model, filters=filters)

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
        return self._api_call(*args, method=self.session.get, **kwargs)

    def post(self, *args, **kwargs):
        return self._api_call(*args, method=self.session.post, **kwargs)

    def put(self, *args, **kwargs):
        return self._api_call(*args, method=self.session.put, **kwargs)

    def delete(self, *args, **kwargs):
        return self._api_call(*args, method=self.session.delete, **kwargs)

    # ungrouped list functions
    def regions(self, *filters):
        """
        Returns the available Regions for Linode products.

        :param filters: Any number of filters to apply to the query.

        :returns: A list of available Regions.
        :rtype: PaginatedList of Region
        """
        return self._get_and_filter(Region, *filters)

    def images(self, *filters):
        """
        Retrieves a list of available Images, including public and private
        Images available to the acting user.  You can filter this query to
        retrieve only Images relevant to a specific query, for example::

           debian_images = client.images(
               Image.vendor == "debain")

        :param filters: Any number of filters to apply to the query.

        :returns: A list of available Images.
        :rtype: PaginatedList of Image
        """
        return self._get_and_filter(Image, *filters)

    def image_create(self, disk, label=None, description=None):
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

    def domains(self, *filters):
        """
        Retrieves all of the Domains the acting user has access to.

        :param filters: Any number of filters to apply to this query.

        :returns: A list of Domains the acting user can access.
        :rtype: PaginatedList of Domain
        """
        return self._get_and_filter(Domain, *filters)

    def nodebalancers(self, *filters):
        """
        Retrieves all of the NodeBalancers the acting user has access to.

        :param filters: Any number of filters to apply to this query.

        :returns: A list of NodeBalancers the acting user can access.
        :rtype: PaginatedList of NodeBalancers
        """
        return self._get_and_filter(NodeBalancer, *filters)

    def nodebalancer_create(self, region, **kwargs):
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

    def domain_create(self, domain, master=True, **kwargs):
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

    def tags(self, *filters):
        """
        Retrieves the Tags on your account.  This may only be attempted by
        unrestricted users.

        :param filters: Any number of filters to apply to this query.

        :returns: A list of Tags on the account.
        :rtype: PaginatedList of Tag
        """
        return self._get_and_filter(Tag, *filters)

    def tag_create(self, label, instances=None, domains=None, nodebalancers=None,
                   volumes=None, entities=[]):
        """
        Creates a new Tag and optionally applies it to the given entities.

        :param label: The label for the new Tag
        :type label: str
        :param entities: A list of objects to apply this Tag to upon creation.
                         May only be taggable types (Linode Instances, Domains,
                         NodeBalancers, or Volumes).  These are applied *in addition
                         to* any IDs specified with ``instances``, ``domains``,
                         ``nodebalancers``, or ``volumes``, and is a convenience
                         for sending multiple entity types without sorting them
                         yourself.
        :type entities: list of Instance, Domain, NodeBalancer, and/or Volume
        :param instances: A list of Linode Instances to apply this Tag to upon
                        creation
        :type instances: list of Instance or list of int
        :param domains: A list of Domains to apply this Tag to upon
                        creation
        :type domains: list of Domain or list of int
        :param nodebalancers: A list of NodeBalancers to apply this Tag to upon
                        creation
        :type nodebalancers: list of NodeBalancer or list of int
        :param volumes: A list of Volumes to apply this Tag to upon
                        creation
        :type volumes: list of Volumes or list of int

        :returns: The new Tag
        :rtype: Tag
        """
        linode_ids, nodebalancer_ids, domain_ids, volume_ids = [], [], [], []

        # filter input into lists of ids
        sorter = zip((linode_ids, nodebalancer_ids, domain_ids, volume_ids),
                     (instances, nodebalancers, domains, volumes))

        for id_list, input_list in sorter:
            # if we got something, we need to find its ID
            if input_list is not None:
                for cur in input_list:
                    if isinstance(cur, int):
                        id_list.append(cur)
                    else:
                        id_list.append(cur.id)

        # filter entities into id lists too
        type_map = {
            Instance: linode_ids,
            NodeBalancer: nodebalancer_ids,
            Domain: domain_ids,
            Volume: volume_ids,
        }

        for e in entities:
            if type(e) in type_map:
                type_map[type(e)].append(e.id)
            else:
                raise ValueError('Unsupported entity type {}'.format(type(e)))

        # finally, omit all id lists that are empty
        params = {
            'label': label,
            'linodes': linode_ids or None,
            'nodebalancers': nodebalancer_ids or None,
            'domains': domain_ids or None,
            'volumes': volume_ids or None,
        }

        result = self.post('/tags', data=params)

        if not 'label' in result:
            raise UnexpectedResponseError('Unexpected response when creating Tag!', json=result)

        t = Tag(self, result['label'], result)
        return t

    def volumes(self, *filters):
        """
        Retrieves the Block Storage Volumes your user has access to.

        :param filters: Any number of filters to apply to this query.

        :returns: A list of Volumes the acting user can access.
        :rtype: PaginatedList of Volume
        """
        return self._get_and_filter(Volume, *filters)

    def volume_create(self, label, region=None, linode=None, size=20, **kwargs):
        """
        Creates a new Block Storage Volume, either in the given Region or
        attached to the given Instance.

        :param label: The label for the new Volume.
        :type label: str
        :param region: The Region to create this Volume in.  Not required if
                       `linode` is provided.
        :type region: Region or str
        :param linode: The Instance to attach this Volume to.  If not given, the
                       new Volume will not be attached to anything.
        :type linode: Instance or int
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

import json
import requests
import pkg_resources
from datetime import datetime

from linode.errors import ApiError, UnexpectedResponseError
from linode import mappings
from linode.objects import *
from linode.objects.filtering import Filter
from linode.util import PaginatedList

package_version = pkg_resources.require("linode-api")[0].version,

class Group:
    def __init__(self, client):
        self.client = client

class LinodeGroup(Group):
    def get_distributions(self, *filters):
        return self.client._get_and_filter(Distribution, *filters)

    def get_types(self, *filters):
        return self.client._get_and_filter(Service, *filters)

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

    def get_volumes(self, *filters):
        return self.client._get_and_filter(Volume, *filters)

    # create things
    def create_instance(self, ltype, region, distribution=None, **kwargs):
        ret_pass = None
        if distribution and not 'root_pass' in kwargs:
            ret_pass = Linode.generate_root_password()
            kwargs['root_pass'] = ret_pass

        if 'root_ssh_key' in kwargs:
            root_ssh_key = kwargs['root_ssh_key']
            accepted_types = ('ssh-dss', 'ssh-rsa', 'ecdsa-sha2-nistp', 'ssh-ed25519')
            if not any([ t for t in accepted_types if root_ssh_key.startswith(t) ]):
                # it doesn't appear to be a key.. is it a path to the key?
                import os
                root_ssh_key = os.path.expanduser(root_ssh_key)
                if os.path.isfile(root_ssh_key):
                    with open(root_ssh_key) as f:
                        kwargs['root_ssh_key'] = "".join([ l.strip() for l in f ])
                else:
                    raise ValueError('root_ssh_key must either be a path to the key file or a '
                                    'raw public key of one of these types: {}'.format(accepted_types))

        params = {
             'type': ltype.id if issubclass(type(ltype), Base) else ltype,
             'region': region.id if issubclass(type(region), Base) else region,
             'distribution': (distribution.id if issubclass(type(distribution), Base) else distribution) if distribution else None,
         }
        params.update(kwargs)

        result = self.client.post('/linode/instances', data=params)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when creating linode!', json=result)

        l = Linode(self.client, result['id'])
        l._populate(result)
        if not ret_pass:
            return l
        else:
            return l, ret_pass

    def create_stackscript(self, label, script, distros, desc=None, public=False, **kwargs):
        distro_list = None
        if type(distros) is list or type(distros) is PaginatedList:
            distro_list = [ d.id if issubclass(type(d), Base) else d for d in distros ]
        elif type(distros) is Distribution:
            distro_list = [ distros.id ]
        elif type(distros) is str:
            distro_list = [ distros ]
        else:
            raise ValueError('distros must be a list of Distributions or a single Distribution')

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
            "distributions": distro_list,
            "is_public": public,
            "script": script_body,
            "description": desc if desc else '',
        }
        params.update(kwargs)

        result = self.client.post('/linode/stackscripts', data=params)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when creating StackScript!', json=result)

        s = StackScript(self.client, result['id'])
        s._populate(result)
        return s

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

    def get_profile(self):
        """
        Returns this token's user's profile.  This is not a listing endpoint.
        """
        result = self.client.get('/account/profile')

        if not 'username' in result:
            raise UnexpectedResponseError('Unexpected response when getting profile!', json=result)

        p = Profile(self.client, result['username'])
        p._populate(result)
        return p

    def get_settings(self):
        """
        Resturns the account settings data for this acocunt.  This is not  a
        listing endpoint.
        """
        result = self.client.get('/account/settings')

        if not 'email' in result:
            raise UnexpectedResponseError('Unexpected response when getting account settings!',
                    json=result)

        s = AccountSettings(self.client, result['email'])
        s._populate(result)
        return s

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

        result = self.client.post('/account/clients', data=params)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when creating OAuth Client!',
                    json=result)

        c = OAuthClient(self.client, result['id'])
        c._populate(result)
        return c

    def get_oauth_tokens(self, *filters):
        """
        Returns the OAuth Tokens active for this user
        """
        return self.client._get_and_filter(OAuthToken, *filters)

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

        t = OAuthToken(self.client, result['id'])
        t._populate(result)
        return t

    def get_users(self, *filters):
        """
        Returns a list of users on this account
        """
        return self.client._get_and_filter(User, *filters)

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

    u = User(self.client, result['username'])
    u._populate(result)
    return u

class NetworkingGroup(Group):
    def get_ipv4(self, *filters):
        return self.client._get_and_filter(IPAddress, *filters)

    def get_ipv6_ranges(self, *filters):
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
            i = IPAddress(self.client, r['address'])
            i._populate(r)
            ips.append(i)

        return ips
    
    def allocate_ip(self, linode):
        result = self.client.post('/networking/ipv4/', data={
            "linode": linode.id if isinstance(linode, Base) else linode,
        })

        if not 'address' in result:
             raise UnexpectedResponseError('Unexpected response when adding IPv4 address!',
                     json=result)

        ip = IPAddress(self.client, result['address'])
        ip._populate(result)
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
            else:
                raise ValueError('Cannot open ticket regarding type {}!'.format(type(regarding)))


        result = self.client.post('/support/tickets', data=params)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when creating ticket!',
                    json=result)

        t = SupportTicket(self.client, result['id'])
        t._populate(result)
        return t

class LinodeClient:
    def __init__(self, token, base_url="https://api.linode.com/v4", user_agent=None):
        self.base_url = base_url
        self._add_user_agent = user_agent
        self.token = token
        self.linode = LinodeGroup(self)
        self.account = AccountGroup(self)
        self.networking = NetworkingGroup(self)
        self.support = SupportGroup(self)

    @property
    def _user_agent(self):
        return '{}python-linode-api/{} {}'.format(
                '{} '.format(self._add_user_agent) if self._add_user_agent else '',
                package_version,
                requests.utils.default_user_agent()
        )

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
            endpoint = endpoint.format(**{ k: str(vars(model)[k]) for k in vars(model) if 'id' in k })
        url = '{}{}'.format(self.base_url, endpoint)
        headers = {
            'Authorization': "token {}".format(self.token),
            'Content-Type': 'application/json',
            'User-Agent': self._user_agent,
        }

        if filters:
            headers['X-Filter'] = json.dumps(filters)

        body = json.dumps(data)

        r = method(url, headers=headers, data=body)

        if 399 < r.status_code < 600:
            j = None
            error_msg = '{}: '.format(r.status_code)
            try:
                j = r.json()
                if 'errors' in j.keys():
                    for e in j['errors']:
                        error_msg += '{}; '.format(e['reason']) \
                                if 'reason' in e.keys() else ''
            except:
                pass
            raise ApiError(error_msg, status=r.status_code, json=j)

        j = r.json()

        return j

    def _get_objects(self, endpoint, cls, model=None, parent_id=None, filters=None):
        json = self.get(endpoint, model=model, filters=filters)

        if not cls.api_name in json:
            return False

        if 'total_pages' in json:
            formatted_endpoint = endpoint
            if model:
                formatted_endpoint = formatted_endpoint.format(**vars(model))
            return mappings.make_paginated_list(json, cls.api_name, self, parent_id=parent_id, \
                    page_url=formatted_endpoint[1:], cls=cls)
        return mappings.make_list(json[cls.api_name], self, parent_id=parent_id, cls=cls)

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

        n = NodeBalancer(self, result['id'])
        n._populate(result)
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

        d = Domain(self, result['id'])
        d._populate(result)
        return d

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
                from linode.objects.filtering import and_
                parsed_filters = and_(*filters).dct
            else:
                parsed_filters = filters[0].dct

        return self._get_objects(obj_type.api_list(), obj_type, filters=parsed_filters)

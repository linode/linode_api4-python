import requests
import json

from linode.api import ApiError
from linode import mappings
from linode.objects import *
from linode.util import PaginatedList

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

    def get_stackscripts(self, *filters):
        return self.client._get_and_filter(StackScript, *filters)

    def get_kernels(self, *filters):
        return self.client._get_and_filter(Kernel, *filters)

    # create things
    def create_instance(self, ltype, datacenter, distribution=None, **kwargs):
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
             'datacenter': datacenter.id if issubclass(type(datacenter), Base) else datacenter,
             'distribution': (distribution.id if issubclass(type(distribution), Base) else distribution) if distribution else None,
         }
        params.update(kwargs)

        result = self.client.post('/linode/instances', data=params)

        if not 'id' in result:
            return result

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
            return result

        s = StackScript(self.client, result['id'])
        s._populate(result)
        return s

class DnsGroup(Group):
    def get_zones(self, *filters):
        return self.client._get_and_filter(DnsZone, *filters)

    def create_zone(self, dnszone, master=True, **kwargs):
        params = {
            'dnszone': dnszone,
            'type': 'master' if master else 'slave',
        }
        params.update(kwargs)

        result = self.client.post('/dns/zones', data=params)

        if not 'id' in result:
            return result

        z = DnsZone(self.client, result['id'])
        z._populate(result)
        return z

class LinodeClient:
    def __init__(self, token, base_url="https://api.alpha.linode.com/v4"):
        self.base_url = base_url
        self.token = token
        self.linode = LinodeGroup(self)
        self.dns = DnsGroup(self)

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
            raise ApiError(error_msg, status=r.status_code)

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
    def get_datacenters(self, *filters):
        return self._get_and_filter(Datacenter, *filters)

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

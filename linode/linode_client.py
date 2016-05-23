import requests
import json

from linode.api import ApiError
from linode import mappings
from linode.objects import Base, Distribution, Linode, DnsZone, StackScript
from linode.util import PaginatedList

class LinodeClient:
    def __init__(self, token, base_url="https://api.linode.com/v4"):
        self.base_url = base_url
        self.token = token

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

    def _get_objects(self, endpoint, prop, model=None, parent_id=None, filters=None):
        json = self.get(endpoint, model=model, filters=filters)

        if not prop in json:
            return False

        if 'total_pages' in json:
            formatted_endpoint = endpoint
            if model:
                formatted_endpoint = formatted_endpoint.format(**vars(model))
            return mappings.make_paginated_list(json, prop, self, parent_id=parent_id, \
                    page_url=formatted_endpoint[1:])
        return mappings.make_list(json[prop], self, parent_id=parent_id)

    def get(self, *args, **kwargs):
        return self._api_call(*args, method=requests.get, **kwargs)

    def post(self, *args, **kwargs):
        return self._api_call(*args, method=requests.post, **kwargs)

    def put(self, *args, **kwargs):
        return self._api_call(*args, method=requests.put, **kwargs)

    def delete(self, *args, **kwargs):
        return self._api_call(*args, method=requests.delete, **kwargs)

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

        return self._get_objects("/{}".format(obj_type), obj_type, filters=parsed_filters)

    def get_distributions(self, *filters):
        return self._get_and_filter('distributions', *filters)

    def get_services(self, *filters):
        return self._get_and_filter('services', *filters)

    def get_datacenters(self, *filters):
        return self._get_and_filter('datacenters', *filters)

    def get_linodes(self, *filters):
        return self._get_and_filter('linodes', *filters)

    def get_stackscripts(self, *filters):
        return self._get_and_filter('stackscripts', *filters)

    def get_kernels(self, *filters):
        return self._get_and_filter('kernels', *filters)

    def get_dnszones(self, *filters):
        return self._get_and_filter('dnszones', *filters)

    # create things
    def create_linode(self, service, datacenter, source=None, **kwargs):
        if not 'linode' in service.service_type:
            raise AttributeError("{} is not a linode service!".format(service.label))

        ret_pass = None
        if type(source) is Distribution and not 'root_pass' in kwargs:
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
             'service': service.id,
             'datacenter': datacenter.id,
             'source': source.id if source else None,
         }
        params.update(kwargs)

        result = self.post('/linodes', data=params)

        if not 'id' in result:
            return result

        l = Linode(self, result['id'])
        l._populate(result)
        if not ret_pass:
            return l
        else:
            return l, ret_pass

    def create_stackscript(self, label, script, distros, desc=None, public=False, **kwargs):
        distro_list = None
        if type(distros) is list or type(distros) is PaginatedList:
            distro_list = [ d.id for d in distros ]
        elif type(distros) is Distribution:
            distro_list = [ distros.id ]
        else:
            raise ValueError('distros must be a list of Distributions of a single Distribution')

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

        result = self.post('/stackscripts', data=params)

        if not 'id' in result:
            return result

        s = StackScript(self, result['id'])
        s._populate(result)
        return s

    def create_dnszone(self, dnszone, master=True, **kwargs):
        params = {
            'dnszone': dnszone,
            'type': 'master' if master else 'slave',
        }
        params.update(kwargs)

        result = self.post('/dnszones', data=params)

        if not 'id' in result:
            return result

        z = DnsZone(self, result['id'])
        z._populate(result)
        return z

import urllib.parse
import requests
import json

from linode.api import ApiError
from linode import mappings
from linode.objects import Base, Distribution, Linode

class LinodeClient:
    def __init__(self, token, base_url="https://api.linode.com/v2"):
        self.base_url = base_url
        self.token = token

    def _api_call(self, endpoint, model=None, method=None, data=None):
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
            'Authorization': self.token,
            'Content-Type': 'application/json',
        }

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

    def _get_objects(self, endpoint, prop, model=None, parent_id=None):
        json = self.get(endpoint, model=model)

        if not prop in json:
            return False

        if 'total_pages' in json:
            return mappings.make_paginated_list(json, prop, self, parent_id=parent_id)
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

    def _get_and_filter(self, obj_type, **filters):
        results = self._get_objects("/{}".format(obj_type), obj_type)

        if filters and len(filters):
            results = self._filter_list(results, **filters)

        return results

    def get_distributions(self, **filters):
        return self._get_and_filter('distributions', **filters)

    def get_services(self, **filters):
        return self._get_and_filter('services', **filters)

    def get_datacenters(self, **filters):
        return self._get_and_filter('datacenters', **filters)

    def get_linodes(self, **filters):
        return self._get_and_filter('linodes', **filters)

    def get_stackscripts(self, **filters):
        return self._get_and_filter('stackscripts', **filters)

    def get_kernels(self, **filters):
        return self._get_and_filter('kernels', **filters)

    def get_zones(self, **filters):
        return self._get_and_filter('zones', **filters)

    # create things
    def create_linode(self, service, datacenter, source=None, **kwargs):
        if not 'linode' in service.service_type:
            raise AttributeError("{} is not a linode service!".format(service.label))

        ret_pass = None
        if type(source) is Distribution and not 'root_pass' in kwargs:
            ret_pass = Linode.generate_root_password()
            kwargs['root_pass'] = ret_pass

        params = {
             'service': service.id,
             'datacenter': datacenter.id,
             'source': source.id if source else None,
         }
        params.update(kwargs)

        result = self.post('/linodes', data=params)

        if not 'linode' in result:
            return result

        l = Linode(self, result['linode']['id'])
        l._populate(result['linode'])
        if not ret_pass:
            return l
        else:
            return l, ret_pass

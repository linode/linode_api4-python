import httplib2
import json

from linode import config
from linode import mappings

h = httplib2.Http()

class ApiError(RuntimeError):
    def __init__(self, message, status=400):
        super(RuntimeError, self).__init__(message)
        self.status=status

def api_call(endpoint, model=None, method="GET", data=None):
    """
    Makes a call to the linode api.  Data should only be given if the method is
    POST or PUT, and should be a dictionary
    """
    if not config.api_token:
        raise RuntimeError("no api token!  Please call linode.initialize") #TODO

    if model:
        endpoint = endpoint.format(**vars(model))
    url = '{}{}'.format(config.base_url, endpoint)
    headers = {
        'Authorization': config.api_token,
        'Content-Type': 'application/json',
    }
    body = json.dumps(data) if data else ''

    resp, content = h.request(url, method=method, body=body, headers=headers)

    j = json.loads(str(content, 'utf-8'))

    if 'error' in j and j['error']:
        if not config.mute_errors:
            raise ApiError(j['reason'], resp['status'])
        else:
            #TODO - log or something?
            return None

    return j

def get_objects(endpoint, prop, model=None, parent_id=None):
    json = api_call(endpoint, model=model)

    if not prop in json:
        return False

    if 'total_pages' in json:
        return mappings.make_paginated_list(json, prop, parent_id=parent_id)
    return mappings.make_list(json[prop], parent_id=parent_id)

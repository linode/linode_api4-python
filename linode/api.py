import httplib2
import json

from linode import config

h = httplib2.Http()

def api_call(endpoint, model=None, method="GET", data=None):
    """
    Makes a call to the linode api.  Data should only be given if the method is
    POST or PUT, and should be a dictionary
    """
    if model:
        endpoint = endpoint.format(**vars(model))
    url = '{}{}'.format(config.base_url, endpoint)
    headers = {
        'Authorization': config.api_token,
        'Content-Type': 'application/json',
    }
    body = json.dumps(data) if data else ''

    resp, content = h.request(url, method=method, body=body, headers=headers)

    # TODO - what if it fails?

    j = json.loads(str(content, 'utf-8'))
    return j

from urllib import request
import json

from linode import config

def api_call(endpoint, model=None, method="GET"):
    if model:
        endpoint = endpoint.format(**vars(model))
    url = '{}{}'.format(config.base_url, endpoint)
    r = request.Request(url)
    r.add_header("Authorization", config.api_token)
    r.method = method
    resp = request.urlopen(r)

    # TODO - what if it fails?

    j = json.loads(str(resp.read(), 'utf-8'))
    return j

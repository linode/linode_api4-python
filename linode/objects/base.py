from urllib import request
import json

from linode import config

class Base(object):
    """
    The Base class knows how to look up api properties of a model, and lazy-load them.
    """
    properties = ()

    def __init__(self):
        self._populated = False

        for prop in type(self).properties:
            setattr(self, prop, None)

    def __getattribute__(self, name):
        if name in type(self).properties and object.__getattribute__(self, name) is None and \
            not self._populated:
            self._populate()

        return object.__getattribute__(self, name)


    def _populate(self):
        url = type(self).api_endpoint.format(**self.__dict__)
        url = '{}{}'.format(config.base_url, url)
        r = request.Request(url)
        r.add_header("Authorization", "token {}".format(config.api_token))
        resp = request.urlopen(r)

        j = json.loads(str(resp.read(), 'utf-8'))
        for key in j:
            if key in type(self).properties:
                setattr(self, key, j[key])

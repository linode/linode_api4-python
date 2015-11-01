from linode.api import api_call
from linode import config

from datetime import datetime

class Property:
    def __init__(self, mutable=False, identifier=False, volatile=False):
        self.mutable = mutable
        self.identifier = identifier
        self.volatile = volatile

class Base(object):
    """
    The Base class knows how to look up api properties of a model, and lazy-load them.
    """
    properties = ()

    def __init__(self):
        self._set('_populated', False)
        self._set('_last_updated', datetime.min)

        for prop in type(self).properties:
            self._set(prop, None)

    def __getattribute__(self, name):
        if name in type(self).properties.keys():
            if (object.__getattribute__(self, name) is None and not self._populated) \
                or (type(self).properties[name].volatile \
                and object.__getattribute__(self, '_last_updated')
                + config.volatile_refresh_timeout < datetime.now()):
                self._populate()

        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name in type(self).properties.keys() and not type(self).properties[name].mutable:
            raise AttributeError("'{}' is not a mutable field of '{}'"
                .format(name, type(self).__name__))
        self._set(name, value)

    def save(self):
        resp = api_call(type(self).api_endpoint, model=self, method="PUT",
            data=self._serialize())

        if 'error' in resp:
            return False
        return True

    def invalidate(self):
        for key in (k for k in type(self).properties.keys() if type(self).properties[k].mutable):
            self._set(key, None)

        self._populated = False

    def _serialize(self):
       return {a: getattr(self, a) for a in type(self).properties}

    def _populate(self):
        json = api_call(type(self).api_endpoint, model=self)

        for key in json:
            if key in (k for k in type(self).properties.keys()
                if not type(self).properties[k].identifier):
                self._set(key, json[key])

        self._set('_last_updated', datetime.now())

    def _set(self, name, value):
        object.__setattr__(self, name, value)

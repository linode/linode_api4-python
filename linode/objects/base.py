from linode.api import api_call

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

    def save(self):
        resp = api_call(type(self).api_endpoint, model=self, method="PUT", data=self._serialize())

        if 'error' in resp:
            return False
        return True

    def invalidate(self):
        #TODO - this doesn't unset fields, so they won't be reloaded.  This can't happen
        # until we can distinguish between mandatory, immutable fields and volitale fileds
        self._populated = False

    def _serialize(self):
       return {a: getattr(self, a) for a in type(self).properties}

    def _populate(self):
        json = api_call(type(self).api_endpoint, model=self)

        for key in json:
            if key in type(self).properties:
                setattr(self, key, json[key])

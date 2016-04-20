from .. import mappings
from .filtering import FilterableMetaclass

from future.utils import with_metaclass
from datetime import datetime, timedelta
import time

# The interval to reload volatile properties
volatile_refresh_timeout = timedelta(seconds=15)

class Property:
    def __init__(self, mutable=False, identifier=False, volatile=False, relationship=False, \
            derived_class=None, is_datetime=False, filterable=False):
        self.mutable = mutable
        self.identifier = identifier
        self.volatile = volatile
        self.relationship = relationship
        self.derived_class = derived_class
        self.is_datetime = is_datetime
        self.filterable = filterable

class MappedObject:
    def __init__(self, **vals):
        self._expand_vals(self.__dict__, **vals)

    def _expand_vals(self, target, **vals):
        for v in vals:
            if type(vals[v]) is dict:
                vals[v] = MappedObject(**vals[v])
            elif type(vals[v]) is list:
                # oh mama
                vals[v] = [ MappedObject(**i) if type(i) is dict else i for i in vals[v] ]
        target.update(vals)

    def __repr__(self):
        return "Mapping containing {}".format(vars(self).keys())

class Base(object, with_metaclass(FilterableMetaclass)):
    """
    The Base class knows how to look up api properties of a model, and lazy-load them.
    """
    properties = {}

    def __init__(self, client, id):
        self._set('_populated', False)
        self._set('_last_updated', datetime.min)
        self._set('_client', client)

        for prop in type(self).properties:
            self._set(prop, None)

        self._set('id', id)

    def __getattribute__(self, name):
        if name in type(self).properties.keys():
            if type(self).properties[name].identifier:
                pass # don't load identifiers from the server, we have those
            elif (object.__getattribute__(self, name) is None and not self._populated \
                    or type(self).properties[name].derived_class) \
                    or (type(self).properties[name].volatile \
                    and object.__getattribute__(self, '_last_updated')
                    + volatile_refresh_timeout < datetime.now()):
                if type(self).properties[name].derived_class:
                    #load derived object(s)
                    self._set(name, type(self).properties[name].derived_class
                            ._api_get_derived(self, getattr(self, '_client')))
                else:
                    self._api_get()

        return object.__getattribute__(self, name)

    def __repr__(self):
        return "{}: {}".format(type(self).__name__, self.id)

    def __setattr__(self, name, value):
        if name in type(self).properties.keys() and not type(self).properties[name].mutable:
            raise AttributeError("'{}' is not a mutable field of '{}'"
                .format(name, type(self).__name__))
        self._set(name, value)

    def save(self):
        resp = self._client.put(type(self).api_endpoint, model=self,
            data=self._serialize())

        if 'error' in resp:
            return False
        return True

    def delete(self):
        resp = self._client.delete(type(self).api_endpoint, model=self)

        if 'error' in resp:
            return False
        self.invalidate()
        return True

    def invalidate(self):
        for key in (k for k in type(self).properties.keys()
            if not type(self).properties[k].identifier):
                self._set(key, None)

        self._populated = False

    def _serialize(self):
       return { a: getattr(self, a) for a in type(self).properties
            if type(self).properties[a].mutable }

    def _api_get(self):
        json = self._client.get(type(self).api_endpoint, model=self)
        self._populate(json)

    def _populate(self, json):
        if not json:
            return

        for key in json:
            if key in (k for k in type(self).properties.keys()
                    if not type(self).properties[k].identifier):
                if type(self).properties[key].relationship  \
                    and not json[key] is None:
                    if isinstance(json[key], list):
                        objs = []
                        for d in json[key]:
                            if not 'id' in d:
                                continue
                            obj = mappings.make(d['id'], getattr(self,'_client'))
                            if obj:
                                obj._populate(d)
                            objs.append(obj)
                        self._set(key, objs)
                    else:
                        if not 'id' in json[key]:
                            continue
                        obj = mappings.make(json[key]['id'], getattr(self,'_client'))
                        if obj:
                            obj._populate(json[key])
                        self._set(key, obj)
                elif type(json[key]) is dict:
                    self._set(key, MappedObject(**json[key]))
                elif type(json[key]) is list:
                    mapping = MappedObject(_list=json[key])
                    self._set(key, mapping._list)
                elif type(self).properties[key].is_datetime:
                    try:
                        t = time.strptime(json[key], "%Y-%m-%dT%H:%M:%S")
                        self._set(key, datetime.fromtimestamp(time.mktime(t)))
                    except:
                        #TODO - handle this better (or log it?)
                        self._set(key, json[key])
                else:
                    self._set(key, json[key])

        self._set('_populated', True)
        self._set('_last_updated', datetime.now())

    def _set(self, name, value):
        object.__setattr__(self, name, value)

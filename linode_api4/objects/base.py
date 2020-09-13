import time
from datetime import datetime, timedelta

from .filtering import FilterableMetaclass


DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


# The interval to reload volatile properties
volatile_refresh_timeout = timedelta(seconds=15)

class Property:
    def __init__(self, mutable=False, identifier=False, volatile=False, relationship=None,
            derived_class=None, is_datetime=False, filterable=False, id_relationship=False,
            slug_relationship=False):
        """
        A Property is an attribute returned from the API, and defines metadata
        about that value.  These are expected to be used as the values of a
        class-level dict named 'properties' in subclasses of Base.

        mutable - This Property should be sent in a call to save()
        identifier - This Property identifies the object in the API
        volatile - Re-query for this Property if the local value is older than the
            volatile refresh timeout
        relationship - The API Object this Property represents
        derived_class - The sub-collection type this Property represents
        is_datetime - True if this Property should be parsed as a datetime.datetime
        filterable - True if the API allows filtering on this property
        id_relationship - This Property should create a relationship with this key as the ID
            (This should be used on fields ending with '_id' only)
        slug_relationship - This property is a slug related for a given type.
        """
        self.mutable = mutable
        self.identifier = identifier
        self.volatile = volatile
        self.relationship = relationship
        self.derived_class = derived_class
        self.is_datetime = is_datetime
        self.filterable = filterable
        self.id_relationship = id_relationship
        self.slug_relationship = slug_relationship

class MappedObject:
    """
    Converts a dict into values accessible with the dot notation.

    object = {
        "this": "that"
    }

    becomes

    object.this # "that"
    """
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
    
    @property
    def dict(self):
        return dict(self.__dict__)

class Base(object, metaclass=FilterableMetaclass):
    """
    The Base class knows how to look up api properties of a model, and lazy-load them.
    """
    properties = {}

    def __init__(self, client, id, json={}):
        self._set('_populated', False)
        self._set('_last_updated', datetime.min)
        self._set('_client', client)

        #: self._raw_json is a copy of the json received from the API on population,
        #: and cannot be relied upon to be current.  Local changes to mutable fields
        #: that have not been saved will not be present, and volatile fields will not
        #: be updated on access.
        self._set('_raw_json', None)

        for prop in type(self).properties:
            self._set(prop, None)

        self._set('id', id)
        if hasattr(type(self), 'id_attribute'):
            self._set(getattr(type(self), 'id_attribute'), id)

        self._populate(json)

    def __getattribute__(self, name):
        """
        Handles lazy-loading/refreshing an object from the server, and
        getting related objects, as defined in this object's 'properties'
        """
        if name in type(self).properties.keys():
            # We are accessing a Property
            if type(self).properties[name].identifier:
                pass # don't load identifiers from the server, we have those
            elif (object.__getattribute__(self, name) is None and not self._populated \
                    or type(self).properties[name].derived_class) \
                    or (type(self).properties[name].volatile \
                    and object.__getattribute__(self, '_last_updated')
                    + volatile_refresh_timeout < datetime.now()):
                # needs to be loaded from the server
                if type(self).properties[name].derived_class:
                    #load derived object(s)
                    self._set(name, type(self).properties[name].derived_class
                            ._api_get_derived(self, getattr(self, '_client')))
                else:
                    self._api_get()
        elif "{}_id".format(name) in type(self).properties.keys():
            # possible id-based relationship
            related_type = type(self).properties['{}_id'.format(name)].id_relationship
            if related_type:
                # no id, no related object
                if not getattr(self, "{}_id".format(name)):
                    return None
                # it is a relationship
                relcache_name = '_{}_relcache'.format(name)
                if not hasattr(self, relcache_name):
                    self._set(relcache_name, related_type(self._client, getattr(self, '{}_id'.format(name))))
                return object.__getattribute__(self, relcache_name)

        return object.__getattribute__(self, name)

    def __repr__(self):
        """
        Returns a safe representation of this object without accessing the server
        """
        return "{}: {}".format(type(self).__name__, self.id)

    def __setattr__(self, name, value):
        """
        Enforces allowing editing of only Properties defined as mutable
        """
        if name in type(self).properties.keys() and not type(self).properties[name].mutable:
            raise AttributeError("'{}' is not a mutable field of '{}'"
                .format(name, type(self).__name__))
        self._set(name, value)

    def save(self):
        """
        Send this object's mutable values to the server in a PUT request
        """
        resp = self._client.put(type(self).api_endpoint, model=self,
            data=self._serialize())

        if 'error' in resp:
            return False
        return True

    def delete(self):
        """
        Sends a DELETE request for this object
        """
        resp = self._client.delete(type(self).api_endpoint, model=self)

        if 'error' in resp:
            return False
        self.invalidate()
        return True

    def invalidate(self):
        """
        Invalidates all non-identifier Properties this object has locally,
        causing the next access to re-fetch them from the server
        """
        for key in [k for k in type(self).properties.keys()
                if not type(self).properties[k].identifier]:
            self._set(key, None)

        self._set('_populated', False)

    def _serialize(self):
        """
        A helper method to build a dict of all mutable Properties of
        this object
        """
        result = { a: getattr(self, a) for a in type(self).properties
            if type(self).properties[a].mutable }

        for k, v in result.items():
            if isinstance(v, Base):
                result[k] = v.id
            elif isinstance(v,MappedObject):
                result[k] = v.dict

        return result

    def _api_get(self):
        """
        A helper method to GET this object from the server
        """
        json = self._client.get(type(self).api_endpoint, model=self)
        self._populate(json)

    def _populate(self, json):
        """
        A helper method that, given a JSON object representing this object,
        assigns values based on the properties dict and the attributes of
        its Properties.
        """
        if not json:
            return

        # hide the raw JSON away in case someone needs it
        self._set('_raw_json', json)

        for key in json:
            if key in (k for k in type(self).properties.keys()
                    if not type(self).properties[k].identifier):
                if type(self).properties[key].relationship \
                    and not json[key] is None:
                    if isinstance(json[key], list):
                        objs = []
                        for d in json[key]:
                            if not 'id' in d:
                                continue
                            new_class = type(self).properties[key].relationship
                            obj = new_class.make_instance(d['id'],
                                    getattr(self,'_client'))
                            if obj:
                                obj._populate(d)
                            objs.append(obj)
                        self._set(key, objs)
                    else:
                        if isinstance(json[key], dict):
                            related_id = json[key]['id']
                        else:
                            related_id = json[key]
                        new_class = type(self).properties[key].relationship
                        obj = new_class.make_instance(related_id, getattr(self,'_client'))
                        if obj and isinstance(json[key], dict):
                            obj._populate(json[key])
                        self._set(key, obj)
                elif  type(self).properties[key].slug_relationship \
                        and not json[key] is None:
                    # create an object of the expected type with the given slug
                    self._set(key, type(self).properties[key].slug_relationship(self._client, json[key]))
                elif type(json[key]) is dict:
                    self._set(key, MappedObject(**json[key]))
                elif type(json[key]) is list:
                    # we're going to use MappedObject's behavior with lists to
                    # expand these, then grab the resulting value to set
                    mapping = MappedObject(_list=json[key])
                    self._set(key, mapping._list) # pylint: disable=no-member
                elif type(self).properties[key].is_datetime:
                    try:
                        t = time.strptime(json[key], DATE_FORMAT)
                        self._set(key, datetime.fromtimestamp(time.mktime(t)))
                    except:
                        # if this came back, there's probably an issue with the
                        # python library; a field was marked as a datetime but
                        # wasn't in the expected format.
                        self._set(key, json[key])
                else:
                    self._set(key, json[key])

        self._set('_populated', True)
        self._set('_last_updated', datetime.now())

    def _set(self, name, value):
        """
        A helper method to set values of Properties without invoking
        the overloaded __setattr__
        """
        object.__setattr__(self, name, value)

    @classmethod
    def api_list(cls):
        """
        Returns a URL that will produce a list of JSON objects
        of this class' type
        """
        return '/'.join(cls.api_endpoint.split('/')[:-1])

    @staticmethod
    def make(id, client, cls, parent_id=None, json=None):
        """
        Makes an api object based on an id and class.

        :param id: The id of the object to create
        :param client: The LinodeClient to give the new object
        :param cls: The class type to instantiate
        :param parent_id: The parent id for derived classes
        :param json: The JSON to use to populate the new class

        :returns: An instance of cls with the given id
        """
        from .dbase import DerivedBase # pylint: disable-all

        if issubclass(cls, DerivedBase):
            return cls(client, id, parent_id, json)
        else:
            return cls(client, id, json)

    @classmethod
    def make_instance(cls, id, client, parent_id=None, json=None):
        """
        Makes an instance of the class this is called on and returns it.

        The intended usage is:
          instance = Linode.make_instance(123, client, json=response)

        :param cls: The class this was called on.
        :param id: The id of the instance to create
        :param client: The client to use for this instance
        :param parent_id: The parent id for derived classes
        :param json: The JSON to populate the instance with

        :returns: A new instance of this type, populated with json
        """
        return Base.make(id, client, cls, parent_id=parent_id, json=json)

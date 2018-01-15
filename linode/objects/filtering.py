def or_(a, b):
    if not isinstance(a, Filter) or not isinstance(b, Filter):
        raise TypeError
    return a.__or__(b)

def and_(a, b):
    return a.__and__(b)

class Filter:
    def __init__(self, dct):
        self.dct = dct

    def __or__(self, other):
        if not isinstance(other, Filter):
            raise TypeError("You can only or Filter types!")
        if '+or' in self.dct:
            return Filter({ '+or': self.dct['+or'] + [ other.dct ] })
        else:
            return Filter({ '+or': [self.dct, other.dct] })

    def __and__(self, other):
        if not isinstance(other, Filter):
            raise TypeError("You can only and Filter types!")
        if '+and' in self.dct:
            return Filter({ '+and': self.dct['+and'] + [ other.dct ] })
        else:
            return Filter({ '+and': [self.dct, other.dct] })

    def order_by(self, field, desc=False):
        # we can't include two order_bys
        if '+order_by' in self.dct:
            raise AssertionError("You may only order by once!")

        if not isinstance(field, FilterableAttribute):
            raise TypeError("Can only order by filterable attributes!")

        self.dct['+order_by'] = field.name
        if desc:
            self.dct['+order'] = 'desc'

        return self

    def limit(self, limit):
        # we can't limit twice
        if '+limit' in self.dct:
            raise AssertionError("You may only limit once!")

        if not type(limit) == int:
            raise TypeError("Limit must be an int!")

        self.dct['+limit'] = limit

        return self

class FilterableAttribute:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return Filter({ self.name: other })

    def __ne__(self, other):
        return Filter({ self.name: { "+ne": other } })

    # "in" evaluates the return value - have to use 
    # type.contains instead
    def contains(self, other):
        return Filter({ self.name: { "+contains": other } })

    def __gt__(self, other):
        return Filter({ self.name: { "+gt": other } })

    def __lt__(self, other):
        return Filter({ self.name: { "+lt": other } })

    def __ge__(self, other):
        return Filter({ self.name: { "+gte": other } })

    def __le__(self, other):
        return Filter({ self.name: { "+lte": other } })

class NonFilterableAttribute:
    """This class is used to provide better error messages should a user attempt
    to filter an object on an attribute that is defined in properties, but is
    not filterable (otherwise they'd see "{} has no attribute {}" which is less
    obvious
    """
    def __init__(self, clsname, atrname):
        self.clsname = clsname
        self.atrname = atrname

    def __eq__(self, other):
        raise AttributeError("{} cannot be filtered by {}".format(self.clsname, self.atrname))

    def __ne__(self, other):
        raise AttributeError("{} cannot be filtered by {}".format(self.clsname, self.atrname))

    def contains(self, other):
        raise AttributeError("{} cannot be filtered by {}".format(self.clsname, self.atrname))

    def __gt__(self, other):
        raise AttributeError("{} cannot be filtered by {}".format(self.clsname, self.atrname))

    def __lt__(self, other):
        raise AttributeError("{} cannot be filtered by {}".format(self.clsname, self.atrname))

    def __ge__(self, other):
        raise AttributeError("{} cannot be filtered by {}".format(self.clsname, self.atrname))

    def __le__(self, other):
        raise AttributeError("{} cannot be filtered by {}".format(self.clsname, self.atrname))

class FilterableMetaclass(type):
    def __init__(cls, name, bases, dct):
        if hasattr(cls, 'properties'):
            for key in cls.properties.keys():
                # TODO - either add NonFilterableAttribute or remove commented code
                #if cls.properties[key].filterable:
                    setattr(cls, key, FilterableAttribute(key)) # pylint: disable=bad-indentation
                #else:
                #    setattr(cls, key, NonFilterableAttribute(cls.__name__, key))

        super(FilterableMetaclass, cls).__init__(name, bases, dct)

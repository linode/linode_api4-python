"""
.. module:: linode

Collections returned by the :any:`LinodeClient` can be filtered using a
SQLAlchemy-like syntax.  When calling any "get" method of the :any:`LinodeClient`
class of one of its groups, any number of filters may be passed in as boolean
comparisons between attributes of the model returned by the collection.

For example, calling :any:`instances` returns a list of :any:`Instance`
objects, so we can use properties of :any:`Instance` to filter the results::

   # returns all Instances in the "prod" group
   client.linode.instances(Instance.group == "prod")

You can use any boolean comparisons when filtering collections::

   # returns all Instances _not_ in us-east-1a
   client.linode.instances(Instance.region != "us-east-1a")

You can combine filters to be even more specific - by default all filters are
considered::

   # returns all Instances in the "prod" group that are in us-east-1a
   client.linode.instances(Instance.group == "prod",
                               Instance.region == "us-east-1a")

If you need to combine the results of two filters, you can use :any:`or_` to define
this relationship::

   # returns all Instance in either the "prod" or "staging" groups
   client.linode.instances(or_(Instance.group == "prod",
                                   Instance.group == "staging"))

:any:`and_` is also available in case you need to do deeply-nested comparisons::

   # returns all Instances in the group "staging" and any Instances in the "prod"
   # group that are located in "us-east-1a"
   client.linode.instances(or_(Instance.group == "staging",
                                   and_(Instance.group == "prod",
                                        Instance.region == "us-east-1a"))

"""


def or_(a, b):
    """
    Combines two :any:`Filters<Filter>` with an "or" operation, matching
    any results that match any of the given filters.

    :param a: The first filter to consider.
    :type a: Filter
    :param b: The second filter to consider.
    :type b: Filter

    :returns: A filter that matches either a or b
    :rtype: Filter
    """
    if not isinstance(a, Filter) or not isinstance(b, Filter):
        raise TypeError
    return a.__or__(b)


def and_(a, b):
    """
    Combines two :any:`Filters<Filter>` with an "and" operation, matching
    any results that match both of the given filters.

    :param a: The first filter to consider.
    :type a: Filter
    :param b: The second filter to consider.
    :type b: Filter

    :returns: A filter that matches both a and b
    :rtype: Filter
    """
    return a.__and__(b)


def order_by(field, desc=False):
    """
    Allows ordering of results.  You may only ever order a collection's results
    once in a given request.  For example::

       # sort results by Instances group
       client.linode.instances(order_by(Instance.group))

    :param field: The field to order results by.  Must be a filterable attribute
                  of the model.
    :type field: FilterableAttribute
    :param desc: If True, return results in descending order.  Defaults to False
    :type desc: bool

    :returns: A filter that will order results as requested.
    :rtype: Filter
    """
    return Filter({}).order_by(field, desc)


def limit(amount):
    """
    Allows limiting of results in a collection.  You may only ever apply a limit
    once per request.  For example::

        # returns my first 5 Instances
        client.linode.instances(limit(5))

    :param amount: The number of results to return.
    :type amount: int

    :returns: A filter that will limit the number of results returned.
    :rtype: Filter
    """
    return Filter({}).limit(amount)


class Filter:
    """
    A Filter represents a comparison to send to the API.  These should not be
    constructed normally, but instead should be returned from comparisons
    between class attributes of filterable classes (see above).  Filters can
    be combined with :any:`and_` and :any:`or_`.
    """
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
        return Filter({ self.name: { "+neq": other } })

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
                setattr(cls, key, FilterableAttribute(key))

        super().__init__(name, bases, dct)

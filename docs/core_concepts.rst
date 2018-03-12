Core Concepts
=============

The linode-api package, and the API V4, have a few ideas that will help you more
quickly become proficient with their usage.

Pagination
----------

The Linode API V4 loosely follows a RESTful design, and paginates results to
responses for GETs to collections.  This library handles pagination transparently,
and does not load pages of data until they are required.  This is handled by
the :py:class:PaginatedList class, which behaves similarly to a python list.
For example:

.. code-block:: python

   linodes = client.linode.get_instances() # returns a PaginatedList of linodes

   first_linode = linodes[0] # the first page is loaded automatically, this does
                             # not emit an API call

   some_linode = linodes[-1] # loads only the last page, if it hasn't been loaded yet
                             # this _will_ emit an API call if there were two or
                             # more pages of results

   for current_linode in linodes: # iterate over all results, loading pages as necessary
       print(current_linode.label)

If you're not concerned about performance, using a :py:class:PaginatedList as
a normal list should be fine.  If your application is sensitive to performance
concerns, be aware that iterating over a :py:class:PaginatedList can cause
the thread to wait as a synchronous request for additional data is made
mid-iteration.

Filtering
---------

Collections of objects in the API can be filtered to make their results more
useful.  For example, you can ask the API for all Linodes you own belonging to
a certain group, instead of having to do this filtering yourself on the full
list.  This library implements filtering with a SQLAlchemy-like syntax, where
every model's attributes may be used in comparisons to generate filters.  For
example:

.. code-block:: python

   prod_linodes = client.linode.get_instances(Linode.group == "production")

Filters may be combined using boolean operators similar to SQLAlchemy:

.. code-block:: python

   # and_ and or_ can be imported from the linode package to combine filters
   from linode import or_
   prod_or_staging = client.linode.get_instances(or_(Linode.group == "production"
                                                     Linode.group == "staging"))

   # and_ isn't strictly necessary, as it's the default when passing multiple
   # filters to a collection
   prod_and_green = client.linode.get_instances(Linode.group == "production",
                                                Linode.label.like("green"))

Filters are generally only applicable for the type of model you are querying,
but can be combined to your heart's content.  For numeric fields, the standard
numeric comparisons are accepted, and work as you'd expect.  See
:py:module:linode.objects.filtering for full details.

Lazy-Loading
------------

Models
------

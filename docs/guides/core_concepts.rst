Core Concepts
=============

.. module:: linode

The linode-api package, and the API V4, have a few ideas that will help you more
quickly become proficient with their usage.  This page assumes you've read the
`Getting Started <getting_started.html>`_ guide, and know the basics of
authentication already.

Pagination
----------

The Linode API V4 loosely follows a RESTful design, and paginates results to
responses for GETs to collections.  This library handles pagination
transparently, and does not load pages of data until they are required.  This
is handled by the :any:`PaginatedList` class, which
behaves similarly to a python list.  For example::

   linodes = client.linode.instances() # returns a PaginatedList of linodes

   first_linode = linodes[0] # the first page is loaded automatically, this does
                             # not emit an API call

   # you can also use the `first()` convenience function for this
   first_linode = linodes.first()

   last_linode = linodes[-1] # loads only the last page, if it hasn't been loaded yet
                             # this _will_ emit an API call if there were two or
                             # more pages of results.  If there was only one page,
                             # this does not emit an additional call

   for current_linode in linodes: # iterate over all results, loading pages as necessary
       print(current_linode.label)

If you're not concerned about performance, using a
:any:`PaginatedList` as a normal list should be fine.  If
your application is sensitive to performance concerns, be aware that iterating
over a :any:`PaginatedList` can cause the thread to wait as a synchronous
request for additional data is made mid-iteration.

Filtering
---------

Collections of objects in the API can be filtered to make their results more
useful.  For example, instead of having to do this filtering yourself on the
full list, you can ask the API for all Linodes you own belonging to a certain
group.  This library implements filtering with a SQLAlchemy-like syntax, where
a model's attributes may be used in comparisons to generate filters.  For
example::

   prod_linodes = client.linode.instances(Linode.group == "production")

Filters may be combined using boolean operators similar to SQLAlchemy::

   # and_ and or_ can be imported from the linode package to combine filters
   from linode import or_
   prod_or_staging = client.linode.instances(or_(Linode.group == "production"
                                                     Linode.group == "staging"))

   # and_ isn't strictly necessary, as it's the default when passing multiple
   # filters to a collection
   prod_and_green = client.linode.instances(Linode.group == "production",
                                                Linode.label.contains("green"))

Filters are generally only applicable for the type of model you are querying,
but can be combined to your heart's content.  For numeric fields, the standard
numeric comparisons are accepted, and work as you'd expect.  See
:doc:`Filtering Collections<../linode/objects/filtering>` for full details.

Models
------

This library represents objects the API returns as "models."  Most methods of
:any:`LinodeClient` return models or lists of models, and all models behave
in a similar manner.

Creating Models
^^^^^^^^^^^^^^^

In addition to looking up models from collections, you can simply import the
model class and create it by ID.::

   from linode import Linode
   my_linode = Linode(client, 123)

All models take a `LinodeClient` as their first parameter, and their ID as the
second.  For derived models (models that belong to another model), the parent
model's ID is taken as a third argument to the constructor (i.e. to construct
a :any:`Disk` you pass a :any:`LinodeClient`, the disk's ID, then the parent
Linode's ID).

Be aware that when creating a model this way, it is _not_ loaded from the API
immediately.  Models in this library are **lazy-loaded**, and will not be looked
up until one of their attributes that is currently unknown is accessed.

Lazy Loading
^^^^^^^^^^^^

If a model is created, but not yet retrieved from the API, its attributes will be
unpopulated.  As soon as an unpopulated attribute is accessed, an API call is
emitted to retrieve that value (and the rest of the attributes in the model) from
the API.  For example::

   my_linode.id # no API call emitted - this was set on creation 
   my_linode.label # API call emitted - entire object is loaded from response
   my_linode.group # no API call emitted - this was loaded above

.. note::

   When loading a model in this fashion, if the model does not exist in the API
   or you do not have access to it, an ApiError is raised.  If you want to load
   a model in a more predictable manner, see :any:`LinodeClient.load`

Volatile Attributes
^^^^^^^^^^^^^^^^^^^

Some attributes of models are marked **volatile**.  A **volatile** attribute will
become stale after a short time, and if accessed when its value is stale, will
refresh itself (and the entire object) from the API to ensure the value is
current.::

   my_linode.boot()
   my_linode.status # booting
   time.sleep(20) # wait for my_linode.status to become stale
   my_linode.status # running


.. note::

   While it is often safe to loop on a **volatile** attribute, be aware that there is
   no guarantee that their value will ever change - be sure that any such loops
   have another exit condition to prevent your application from hanging if something
   you didn't expect happens.

Updating and Deleting Models
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Most models have some number of mutable attributes.  Updating a model is as simple
as assigning a new value to these attributes and then saving the model.  Many
models can also be deleted in a similar fashion.::

   my_linode.label = "new-label"
   my_linode.group = "new-group"
   my_linode.save() # emits an API call to update label and group

   my_linode.delete() # emits an API call to delete my_linode

.. note::

   Saving a model *may* fail if the values you are attempting to save are invalid.
   If the values you are attemting to save are coming from an untrusted source,
   be sure to handle a potential :any:`ApiError` raised by the API returning
   an unsuccessful response code.

Relationships
^^^^^^^^^^^^^

Many models are related to other models (for example a Linode has disks, configs,
volumes, backups, a region, etc).  Related attributes are accessed like
any other attribute on the model, and will emit an API call to retrieve the
related models if necessary.::

   len(my_linode.disks) # emits an API call to retrieve related disks
   my_linode.disks[0] # no API call emitted - this is already loaded

   my_linode.region.id # no API call emitted - IDs are already populated
   my_linode.region.country # API call emitted - retrieves region object

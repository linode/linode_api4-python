Getting Started
===============

Installation
------------

The linode_api4 package can be installed from pypi as shown below:

.. code-block:: shell

   pip install linode_api4

If you prefer, you can clone the package from github_ and install it from source:

.. _github: https://github.com/Linode/linode_api4-python

.. code-block:: shell

   git clone git@github.com:Linode/linode_api4-python
   cd linode_api4
   python -m pip install .

Authentication
--------------

In order to make requests to the Linode API, you will need a token.  To generate
one,  log in to cloud.linode.com_, and on your profile_ click "Create a Personal
Access Token".

.. _cloud.linode.com: https://cloud.linode.com
.. _profile: https://cloud.linode.com/profile/tokens

.. note::
   You can also use an OAuth Token to authenticate to the API - see :doc:`OAuth<oauth>`
   for details.

When creating a Personal Access Token, you will be prompted for what scopes the
token should be created with.  These scopes control what parts of your account
this token may be used to access - for more information, see :ref:`OAuth Scopes<oauth_scopes>`.
Restricting what a token can access is more secure than creating one with access
to your entire account, but can be less convenient since you would need to create
a new token to access other parts of the account.  For the examples on this page,
your Personal Access Token must be able to view and create Linode Instances.

Listing your Linode Instances
-----------------------------

Using the token you generated above, create a :py:class:`LinodeClient` object
that will be used for all interactions with the API.::

   from linode_api4 import LinodeClient
   client = LinodeClient(token)

This object will manage all requests you make through the API.  Once it's
set up, you can use it to retrieve and print a list of your Linode Instances::

   my_linodes = client.linode.instances()

   for current_linode in my_linodes:
       print(current_linode.label)

When retrieving collections of objects from the API, a list-like object is
returned, and may be iterated over or indexed as a normal list.

Creating a Linode Instance
--------------------------

In order to create a Linode Instance, we need a few pieces of information:

 * what :any:`Region` to create the Instance in.
 * what :any:`Type` of Instance to create.
 * what :any:`Image` to deploy to the new Instance.

We can query for these values similarly to how we listed our Linode Instances
above::

   available_regions = client.regions()

We could also use values that we know in advance to avoid the need to query the
API.  For example, we may know that we want a `g6-standard-4` Instance running
the `linode/debian9` Image.  Both objects and IDs are accepted when creating an
Instance.::

   chosen_region = available_regions[0]


   new_linode, password = client.linode.instance_create('g5-standard-4',
                                                        chosen_region,
                                                        image='linode/debian9')

:py:func:`instance_create` returns the newly-created Instance object and the
root password that was generated for it.  This Instance will boot automatically,
and should be available shortly.  Finally, let's print out the results so we
can access our new server.

.. code-block:: python

   print("ssh root@{} - {}".format(new_linode.ipv4[0], password))

Continue on to `Core Concepts <core_concepts.html>`_

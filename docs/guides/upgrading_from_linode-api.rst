Upgrading from linode-api
=========================

.. package:: linode_api4

.. highlight:: python

This library was previously released as ``linode-api``, which is still
available as a `branch on the linode_api4 github`_.  If you used the 
``linode-api`` package previously and would like to upgrade your scripts
to use ``linode_api4``, this guide is for you.

.. _branch on the linode_api4 github: https://github.com/linode/linode_api4-python/tree/linode-api

New Dependency and Imports
--------------------------

This package is now called ``linode_api4``.  In any ``setup.py`` or
``requirements.txt`` you have in your project, change ``linode-api`` to
``linode_api4``.

The module you import in your classes has changed from ``linode`` to
``linode_api4`` to match the package name.

Renamed Linode Class
--------------------

The ``Linode`` class has been renamed to :any:`Instance` to match the upstream
naming convention.  If your script looks like this::

   from linode import LinodeClient, Linode

   client = LinodeClient(token)
   linode = client.load(Linode, 123)

You should change it to this::

   from linode_api4 import LinodeClient, Instance

   client = LinodeClient(token)
   instance = client.load(Instance, 123)

New Method Naming Scheme
------------------------

Methods used to retrieve or create objects now follow a "noun-verb" convention
instead of the previous "verb-noun" convention. For example, the
``create_domain`` method to create a new :any:`Domain` is now
``domain_create``.

Additionally, the ``get_`` prefix has been dropped from methods returning lists
of objects.  The ``domains`` method replaces the old method name ``get_domains``.

If your code looked like this::

   from linode import LinodeClient, Linode

   client = LinodeClient(token)

   linodes = client.linode.get_instances()
   print("You have {} Linodes".format(len(linodes)))

   new_linode, password = client.linode.create_instance('g6-standard-2', 'us-east',
                                                        image='linode/debian9')

   print("Now you have {} Linodes".format(len(linodes)+1))
   print("Your new Linode's ip address is {}".format(new_linode.ipv4[0]))

It would be changed to this::

   from linode_api4 import LinodeClient, Instance

   client = LinodeClient(token)

   instances = client.linode.instances()
   print("You have {} Linode Instances".format(len(instances))

   new_instance, password = client.linode.instance_create('g6-standard-2', 'us-east',
                                                          image='linode/debian9')

   print("Now you have {} Linode Instances".format(len(instances)+1))
   print("Your new Instance's ip address is {}".format(new_instance.ipv4[0]))

New Package Structure
---------------------

.. note::
   The imports that need to be changed were never the recommended way of
   importing classes, and all recommended, documented import schemes still work
   without change.

In the unlikely case that you are importing classes from deep within the
``linode.objects`` package, you may need to change your imports to match the
new package structure.  For example, if your code currently does this::

   from linode import LinodeClient
   from linode.objects.linode.linode import Linode
   from linode.objects.linode.disk import Disk

You will need to change it to this::

   from linode import LinodeClient
   from linode.objects.linode import Instance, Disk

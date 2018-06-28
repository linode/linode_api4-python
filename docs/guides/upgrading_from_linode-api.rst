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

Methods used to retrieve or create objects used to conform to a "verb-noun"
naming scheme.  For example, ``create_domain`` was used to create a new Domain
in Linode's DNS Manager.  This has been renamed to ``domain_create`` to conform
to the new, "noun-verb" naming convention.  Methods that used to begin with
"`get_`" simply dropped the prefix, making  ``get_domains`` into ``domians``.

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
   The imports that need to be changed were never the recomended way of
   importing classes, and all recoomended, documented import schemes still work
   without change.

In the unlikely case that  you are importing classes from deep within the
``linode.objects`` package, you may need to change your imports to match the
new package structure.  For example, if your code currently does this::

   from linode import LinodeClient
   from linode.objects.linode.linode import Linode
   from linode.objects.linode.disk import Disk

You will need to change it to this::

   from linode import LinodeClient
   from linode.objects.linode import Instance, Disk

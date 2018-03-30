Linode Client
=============

.. module:: linode

The LinodeClient is responsible for managing your connection to the API using
your token.  A LinodeClient is required for all connections to the API, and a
reference to one is required by every model.  A LinodeClient is created with a
token, either an OAuth Token from the OAuth Exchange (see
:doc:`oauth<../guides/oauth>` for more information) or a Personal Access Token.
See our :doc:`getting_started<../guides/getting_started>` guide for more
information::

   from linode import LinodeClient

   token = "api-token" # your token goes here

   client = LinodeClient(token)

Grouping
--------

The LinodeClient class is divided into groups following the API's overall
design - some methods and functions are accessible only through members of the
LinodeClient class::

   # access an ungrouped member
   client.get_regions() # /regions

   # access a grouped member - note the URL matches the grouping
   client.linode.get_instances() # /linode/instances

The LinodeClient itself holds top-level collections of the API, while anything
that exists under a group in the API belongs to a member of the client.

LinodeClient class
------------------

.. autoclass:: LinodeClient
   :members:

   .. automethod:: __init__ 

Groups
------

These groups are accessed off of the :any:`LinodeClient` class by name.  For
example::

   client.linode.get_instances()

See :any:`LinodeClient` for more information on the naming of these groups,
although generally they are named the same as the first word of the group.

LinodeGroup
^^^^^^^^^^^

Includes methods for managing and creating Linodes, as well as accessing and
working with associated features.

.. autoclass:: linode.linode_client.LinodeGroup
   :members:

AccountGroup
^^^^^^^^^^^^

Includes methods for managing your account.

.. autoclass:: linode.linode_client.AccountGroup
   :members:

ProfileGroup
^^^^^^^^^^^^

Includes methods for managing your user.

.. autoclass:: linode.linode_client.ProfileGroup
   :members:

NetworkingGroup
^^^^^^^^^^^^^^^

Includes methods for managing your networking systems.

.. autoclass:: linode.linode_client.NetworkingGroup
   :members:

LongviewGroup
^^^^^^^^^^^^^

Includes methods for interacting with our Longview service.

.. autoclass:: linode.linode_client.LongviewGroup
   :members:

SupportGroup
^^^^^^^^^^^^

Includes methods for viewing and opening tickets with our support department.

.. autoclass:: linode.linode_client.SupportGroup
   :members:

Linode Client
=============

.. module:: linode_api4

The LinodeClient is responsible for managing your connection to the API using
your token.  A LinodeClient is required for all connections to the API, and a
reference to one is required by every model.  A LinodeClient is created with a
token, either an OAuth Token from the OAuth Exchange (see
:doc:`oauth<../guides/oauth>` for more information) or a Personal Access Token.
See our :doc:`getting_started<../guides/getting_started>` guide for more
information::

   from linode_api4 import LinodeClient

   token = "api-token" # your token goes here

   client = LinodeClient(token)

Grouping
--------

The LinodeClient class is divided into groups following the API's overall
design - some methods and functions are accessible only through members of the
LinodeClient class::

   # access an ungrouped member
   client.regions() # /regions

   # access a grouped member - note the URL matches the grouping
   client.linode.instances() # /linode/instances

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

   client.linode.instances()

See :any:`LinodeClient` for more information on the naming of these groups,
although generally they are named the same as the first word of the group.

LinodeGroup
^^^^^^^^^^^

Includes methods for managing and creating Linode Instances, as well as
accessing and working with associated features.

.. autoclass:: linode_api4.linode_client.LinodeGroup
   :members:

AccountGroup
^^^^^^^^^^^^

Includes methods for managing your account.

.. autoclass:: linode_api4.linode_client.AccountGroup
   :members:

ProfileGroup
^^^^^^^^^^^^

Includes methods for managing your user.

.. autoclass:: linode_api4.linode_client.ProfileGroup
   :members:

NetworkingGroup
^^^^^^^^^^^^^^^

Includes methods for managing your networking systems.

.. autoclass:: linode_api4.linode_client.NetworkingGroup
   :members:

LongviewGroup
^^^^^^^^^^^^^

Includes methods for interacting with our Longview service.

.. autoclass:: linode_api4.linode_client.LongviewGroup
   :members:

ObjectStorageGroup
^^^^^^^^^^^^^^^^^^

Includes methods for interacting with Linode Objects Storage.  For interacting
with buckets and objects, use the s3 API directly with a library like `boto3`_.

.. autoclass:: linode_api4.linode_client.ObjectStorageGroup
   :members:

.. _boto3: https://github.com/boto/boto3

SupportGroup
^^^^^^^^^^^^

Includes methods for viewing and opening tickets with our support department.

.. autoclass:: linode_api4.linode_client.SupportGroup
   :members:

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

AccountGroup
^^^^^^^^^^^^

Includes methods for managing your account.

.. autoclass:: linode_api4.linode_client.AccountGroup
   :members:
   :special-members:

DatabaseGroup
^^^^^^^^^^^^^

Includes methods for managing Linode Managed Databases.

.. autoclass:: linode_api4.linode_client.DatabaseGroup
   :members:
   :special-members:

DomainGroup
^^^^^^^^^^^

Includes methods for managing Linode Domains.

.. autoclass:: linode_api4.linode_client.DomainGroup
   :members:
   :special-members:

ImageGroup
^^^^^^^^^^

Includes methods for managing Linode Images.

.. autoclass:: linode_api4.linode_client.ImageGroup
   :members:
   :special-members:

LinodeGroup
^^^^^^^^^^^

Includes methods for managing and creating Linode Instances, as well as
accessing and working with associated features.

.. autoclass:: linode_api4.linode_client.LinodeGroup
   :members:
   :special-members:

LKE Group
^^^^^^^^^

Includes methods for interacting with Linode Kubernetes Engine.

.. autoclass:: linode_api4.linode_client.LKEGroup
   :members:
   :special-members:

LongviewGroup
^^^^^^^^^^^^^

Includes methods for interacting with our Longview service.

.. autoclass:: linode_api4.linode_client.LongviewGroup
   :members:
   :special-members:

NetworkingGroup
^^^^^^^^^^^^^^^

Includes methods for managing your networking systems.

.. autoclass:: linode_api4.linode_client.NetworkingGroup
   :members:
   :special-members:

NodeBalancerGroup
^^^^^^^^^^^^^^^^^

Includes methods for managing Linode NodeBalancers.

.. autoclass:: linode_api4.linode_client.NodeBalancerGroup
   :members:
   :special-members:

ObjectStorageGroup
^^^^^^^^^^^^^^^^^^

Includes methods for interacting with Linode Objects Storage.  For interacting
with buckets and objects, use the s3 API directly with a library like `boto3`_.

.. autoclass:: linode_api4.linode_client.ObjectStorageGroup
   :members:
   :special-members:

.. _boto3: https://github.com/boto/boto3

ProfileGroup
^^^^^^^^^^^^

Includes methods for managing your user.

.. autoclass:: linode_api4.linode_client.ProfileGroup
   :members:
   :special-members:

RegionGroup
^^^^^^^^^^^

Includes methods for accessing information about Linode Regions.

.. autoclass:: linode_api4.linode_client.RegionGroup
   :members:
   :special-members:

SupportGroup
^^^^^^^^^^^^

Includes methods for viewing and opening tickets with our support department.

.. autoclass:: linode_api4.linode_client.SupportGroup
   :members:
   :special-members:

TagGroup
^^^^^^^^

Includes methods for managing Linode Tags.

.. autoclass:: linode_api4.linode_client.TagGroup
   :members:
   :special-members:

VolumeGroup
^^^^^^^^^^^

Includes methods for managing Linode Volumes.

.. autoclass:: linode_api4.linode_client.VolumeGroup
   :members:
   :special-members:

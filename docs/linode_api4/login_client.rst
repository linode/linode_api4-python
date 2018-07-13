Linode Login Client
===================

.. module:: linode_api4

The :any:`LinodeLoginClient` is the primary interface to the
`login.linode.com`_ OAuth service, and only needs to be used if writing an
OAuth application.  For an example OAuth application, see `Install on Linode`_,
and for a more comprehensive overview of OAuth, read our :doc:`OAuth
guide<../guides/oauth>`.

.. _login.linode.com: https://login.linode.com
.. _Install on Linode: https://github.com/linode/linode_api4-python/tree/master/examples/install-on-linode

LinodeLoginClient class
-----------------------

Your interface to Linode's OAuth authentication server.

.. autoclass:: linode_api4.LinodeLoginClient
   :members:
   
   .. automethod:: __init__

OAuth Scopes
------------

When requesting authorization to a user's account, OAuth Scopes allow you to
specify the level of access you are requesting.

.. autoclass:: linode_api4.login_client.OAuthScopes
   :members:

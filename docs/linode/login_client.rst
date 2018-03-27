Linode Login Client
===================

.. module:: linode

The :any:`LinodeLoginClient` is the primary interface to the `login.linode.com`_
OAuth service, and need only be used if writing an OAuth application.  For an
example OAuth application, see `Install on Linode`_, and for a more comprehensive
overview of OAuth, read our :doc:`OAuth guide<../guides/oauth>`.

.. _login.linode.com: https://login.linode.com
.. _Install on Linode: https://github.com/linode/python-linode-api/tree/master/examples/install-on-linode

LinodeLoginClient class
-----------------------

Your interface to Linode's OAuth authentication server.

.. autoclass:: linode.LinodeLoginClient
   :members:
   
   .. automethod:: __init__

OAuth Scopes
------------

When requesting authorization to a user's account, OAuth Scopes allow you to
specify the level of access you are requesting.

.. autoclass:: linode.login_client.OAuthScopes
   :members:

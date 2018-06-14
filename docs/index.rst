linode-api
==========

.. note::
   These docs are currently in development, and are therefore incomplete.
   For full documentation of the API, see the `Official API Documentation`_.

   .. _Official API Documentation: https://developers.linode.com/api/v4

This is the documentation for the official Python bindings of the Linode
API.  For API documentation, see `developers.linode.com`_.

This library can be used to interact with all features of the Linode API, and
is compatible with Python 2 and 3.

.. _developers.linode.com: https://developers.linode.com/api/v4

Installation
------------

To install through pypi::

   pip install linode-api

To install from source::

  git clone https://github.com/linode/linode-api-python
  cd python-linode-api
  python setup.py install

For more information, see our :doc:`Getting Started<guides/getting_started>`
guide.

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2

   guides/getting_started
   guides/core_concepts
   guides/oauth
   linode_api/linode_client
   linode_api/login_client
   linode_api/paginated_list
   linode_api/objects/filtering

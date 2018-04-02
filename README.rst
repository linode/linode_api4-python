python-linode-api
=================

The official python library for the `Linode API v4`_ in python.

.. _Linode API v4: https://developers.linode.com/v4/introduction

.. image:: https://travis-ci.org/linode/python-linode-api.svg?branch=master
    :target: https://travis-ci.org/linode/python-linode-api

.. image:: https://badge.fury.io/py/linode-api.svg
    :target: https://badge.fury.io/py/linode-api

Installation
------------
::

    pip install linode-api

Building from Source
--------------------

To build and install this package:

- Clone this repository
- ``./setup.py install``

This package uses the ``linode`` namespace.  This could conflict with libraries
intended for previous versions of the Linode API.  Please be cautious when
installing packages for both version of the API on the same machine.

Usage
-----

Check out the `Getting Started guide`_ to start using this library, or read
`the docs`_ for extensive documentation.

.. _Getting Started guide: http://python-linode-api.readthedocs.io/en/latest/guides/getting_started.html
.. _the docs: http://python-linode-api.readthedocs.io/en/latest/index.html

Examples
--------

See the `Install on a Linode`_ example project for a simple use case demonstrating
many of the features of this library.

.. _Install on a Linode: https://github.com/linode/python-api/tree/master/examples/install-on-linode

Contributing
============

Tests
-----

Tests live in the ``tests`` directory.  To run tests, use setup.py:

.. code-block:: shell

   python setup.py test

The test suite uses fixtures stored as JSON in ``test/fixtures``.  These files
contain sanitized JSON responses from the API - the file name is the URL called
to produce the response, replacing any slashes with underscores.

Test classes should extend ``test.base.ClientBaseCase``.  This provides them
with ``self.client``, a ``LinodeClient`` object that is set up to work with
tests.  Importantly, any GET request made by this object will be mocked to
retrieve data from the test fixtures.  This includes lazy-loaded objects using
this client (and by extension related models).

When testing against requests other than GET requests, ``self.mock_post`` (and
equivalent methods for other HTTP verbs) can be used in a ``with`` block to
mock out the intended request type - include the URL whose response should be
used returned from the fixtures.  For example:

.. code-block:: python

   with self.mock_post('/linode/instances/123'):
     linode = self.client.linode.create_instance('g5-standard-1', 'us-east')
     self.assertEqual(linode.id, 123) # passes

Documentation
-------------

This library is documented with Sphinx_.  Docs live in the ``docs`` directory.
The easiest way to build the docs is to run ``sphinx-autobuild`` in that
folder.

Classes and functions inside the library should be annotated with sphinx-compliant
docstrings which will be used to automatically generate documentation for the
library.  When contributing, be sure to update documentation or include new
docstrings where applicable to keep the library's documentation up to date
and useful.

**Missing or inaccurate documentation is a bug**.  If you notice that the
documentation for this library is out of date or unclear, please
`open an issue`_ to make us aware of the problem.

.. _Sphinx: http://www.sphinx-doc.org/en/master/index.html
.. _open an issue: https://github.com/linode/python-linode-api/issues/new

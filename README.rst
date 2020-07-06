linode_api4
===========

The official python library for the `Linode API v4`_ in python.

**This library is currently in beta.**

.. _Linode API v4: https://developers.linode.com/api/v4/

.. image:: https://travis-ci.com/linode/linode_api4-python.svg?branch=master
    :target: https://travis-ci.com/linode/linode_api4-python

.. image:: https://badge.fury.io/py/linode-api4.svg
   :target: https://badge.fury.io/py/linode-api4

.. image:: https://readthedocs.org/projects/linode-api4/badge/?version=latest
   :target: https://linode-api4.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

Installation
------------
::

    pip install linode_api4

Building from Source
--------------------

To build and install this package:

- Clone this repository
- ``./setup.py install``

Usage
-----

Check out the `Getting Started guide`_ to start using this library, or read
`the docs`_ for extensive documentation.

.. _Getting Started guide: http://linode_api4.readthedocs.io/en/latest/guides/getting_started.html
.. _the docs: http://linode_api4.readthedocs.io/en/latest/index.html

Examples
--------

See the `Install on a Linode`_ example project for a simple use case demonstrating
many of the features of this library.

.. _Install on a Linode: https://github.com/linode/linode_api4-python/tree/master/examples/install-on-linode

Contributing
============

Tests
-----

Tests live in the ``tests`` directory.  When invoking tests, make sure you are
in the root directory of this project.  To run the full suite across all
supported python versions, use tox_:

.. code-block:: shell

   tox

Running tox also runs pylint and coverage reports.

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
mock out the intended request type.  These functions accept the relative path
from the api base url that should be returned, for example::

   # this should return the result of GET /linode/instances/123
   with self.mock_post('/linode/instances/123'):
     linode = self.client.linode.instance_create('g6-standard-2', 'us-east')
     self.assertEqual(linode.id, 123) # passes

.. _tox: http://tox.readthedocs.io

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
.. _open an issue: https://github.com/linode/linode_api4-python/issues/new

linode_api4
===========

The official python library for the `Linode API v4`_ in python.

.. _Linode API v4: https://developers.linode.com/api/v4/

.. image:: https://img.shields.io/github/actions/workflow/status/linode/linode_api4-python/main.yml?label=tests
    :target: https://img.shields.io/github/actions/workflow/status/linode/linode_api4-python/main.yml?label=tests

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
- ``python3 -m pip install .``

Usage
=====

Quick Start
-----------

In order to authenticate with the Linode API, you will first need to create a
`Linode Personal Access Token`_ with your desired account permissions.

The following code sample can help you quickly get started using this package.

.. code-block:: python

    from linode_api4 import LinodeClient, Instance

    # Create a Linode API client
    client = LinodeClient("MY_PERSONAL_ACCESS_TOKEN")

    # Create a new Linode
    new_linode, root_pass = client.linode.instance_create(
        ltype="g6-nanode-1",
        region="us-southeast",
        image="linode/ubuntu22.04",
        label="my-ubuntu-linode"
    )

    # Print info about the Linode
    print("Linode IP:", new_linode.ipv4[0])
    print("Linode Root Password:", root_pass)

    # List all Linodes on the account
    my_linodes = client.linode.instances()

    # Print the Label of every Linode on the account
    print("All Instances:")
    for instance in my_linodes:
        print(instance.label)

    # List Linodes in the us-southeast region
    specific_linodes = client.linode.instances(
        Instance.region == "us-southeast"
    )

    # Print the label of each Linode in us-southeast
    print("Instances in us-southeast:")
    for instance in specific_linodes:
        print(instance.label)

    # Delete the new instance
    new_linode.delete()

Check out the `Getting Started guide`_ for more details on getting started
with this library, or read `the docs`_ for more extensive documentation.

.. _Linode Personal Access Token: https://www.linode.com/docs/products/tools/api/guides/manage-api-tokens/
.. _Getting Started guide: https://linode-api4.readthedocs.io/en/latest/guides/getting_started.html
.. _the docs: https://linode-api4.readthedocs.io/en/latest/index.html

Examples
--------

See the `Install on a Linode`_ example project for a simple use case demonstrating
many of the features of this library.

.. _Install on a Linode: https://github.com/linode/linode_api4-python/tree/master/examples/install-on-linode

Contributing
============

Tests
-----

Tests live in the ``test`` directory.  When invoking tests, make sure you are
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


Integration Tests
-----------------
Integration tests live in the ``test/integration`` directory.

Pre-requisite
^^^^^^^^^^^^^^^^^
Export Linode API token as `LINODE_TOKEN` before running integration tests::

    export LINODE_TOKEN = $(your_token)

Running the tests
^^^^^^^^^^^^^^^^^
Run the tests locally using the make command. Run the entire test suite using command below::

    make testint

To run a specific package, use environment variable `INTEGRATION_TEST_PATH` with `testint` command::

    make INTEGRATION_TEST_PATH="linode_client" testint

To run a specific model test suite, set the environment variable `TEST_MODEL` using file name in `integration/models`::

    make TEST_MODEL="test_account.py" testint

Lastly to run a specific test case use environment variable `TEST_CASE` with `testint` command::

    make TEST_CASE=test_get_domain_record testint

Documentation
-------------

This library is documented with Sphinx_.  Docs live in the ``docs`` directory.
The easiest way to build the docs is to run ``sphinx-autobuild`` in that
folder::

    sphinx-autobuild docs docs/build

After running this command, ``sphinx-autobuild`` will host a local web server
with the rendered documentation.

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

Contributing
------------

Please follow the `Contributing Guidelines`_ when making a contribution.

.. _Contributing Guidelines: https://github.com/linode/linode_api4-python/blob/master/CONTRIBUTING.md

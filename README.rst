Linode SDK: Python
==================

The official python SDK for the `Linode API v2`_ in python3.

Installation
------------
::

    pip3 install linode-sdk

Usage
-----
::

    from linode import linode_client
    
    lc = LinodeClient('my-api-token-here')
    l = lc.get_linodes(label='my-cool-linode')[0]
    l.boot()

Examples
--------

See the `Install on a Linode`_ example project for a simple use case demonstrating
all of the concepts of the SDK.

.. _Linode API v2: http://developers.linode.com
.. _Install on a Linode: http://example.org

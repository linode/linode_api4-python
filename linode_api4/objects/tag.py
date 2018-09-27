from __future__ import absolute_import

import string
import sys
from datetime import datetime
from enum import Enum
from os import urandom
from random import randint

from linode_api4.errors import UnexpectedResponseError
from linode_api4.paginated_list import PaginatedList
from linode_api4.objects import Base, DerivedBase, Property, Instance

class Tag(Base):
    api_endpoint = '/tags/{label}'
    id_attribute = 'label'

    properties = {
        'label': Property(identifier=True),
    }

    def _get_raw_objects(self):
        """
        Helper function to populate the first page of raw objects for this tag.
        This has the side effect of creating the ``_raw_objects`` attribute of
        this object.
        """
        if not hasattr(self, '_raw_objects'):
            result = self._client.get(type(self).api_endpoint, model=self)

            # I want to cache this to avoid making duplicate requests, but I don't
            # want it in the __init__
            self._raw_objects = result # pylint: disable=attribute-defined-outside-init

    def _api_get(self):
        """
        Override the default behavior and just return myself if I exist - this
        is how the python library works, but calling a GET to this endpoint in
        the API returns a collection of objects with this tag.  See ``objects``
        below.
        """
        # do this to allow appropriate 404ing if this tag doesn't exist
        self._get_raw_objects()

        return self

    @property
    def objects(self):
        """
        Returns a list of objects that have been given this tag.  Right now this
        is only Linodes, but in the future this may expand to be more.
        """
        self._get_raw_objects()

        # we need to give the URL of this object to the PaginatedList
        page_url = type(self).api_endpoint.format(**vars(self))

        objects_data = [o['data'] for o in self._raw_objects['data']]
        processed_objects = {
            'page': self._raw_objects['page'],
            'pages': self._raw_objects['pages'],
            'results': self._raw_objects['results'],
            'data': objects_data,
        }

        # return a PaginatedList of objects
        return PaginatedList.make_paginated_list(processed_objects, self._client,
                                                 Instance, page_url=page_url)

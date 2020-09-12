import string
import sys
from datetime import datetime
from enum import Enum
from os import urandom
from random import randint

from linode_api4.errors import UnexpectedResponseError
from linode_api4.paginated_list import PaginatedList
from linode_api4.objects import (Base, DerivedBase, Property, Instance, Volume,
                                 NodeBalancer, Domain)


CLASS_MAP = {
    'linode': Instance,
    'domain': Domain,
    'nodebalancer': NodeBalancer,
    'volume': Volume,
}


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

        return self._raw_objects

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
        Returns a list of objects with this Tag.  This list may contain any
        taggable object type.
        """
        data = self._get_raw_objects()

        return PaginatedList.make_paginated_list(data, self._client, TaggedObjectProxy,
                                                 page_url=type(self).api_endpoint.format(**vars(self)))


class TaggedObjectProxy:
    """
    This class accepts an object from a list of Tagged objects and returns
    the correct type of object based on the response data.

    .. warning::

       It is incorrect to instantiate this class.  This class is a proxy for the
       enveloped objects returned from the tagged objects collection, and should
       only be used in that context.
    """
    id_attribute = 'type' # the envelope containing tagged objects has a `type` field
                          # that defined what type of object is in the envelope.  We'll
                          # use that as the ID for the proxy class so ``make_instance``
                          # below can easily tell what type it should actually be
                          # making and returning.

    @classmethod
    def make_instance(cls, id, client, parent_id=None, json=None):
        """
        Overrides Base's ``make_instance`` to allow dynamic creation of objects
        based on the defined type in the response json.

        :param cls: The class this was called on
        :param id: The id of the instance to create
        :param client: The client to use for this instance
        :param parent_id: The parent id for derived classes
        :param json: The JSON to populate the instance with

        :returns: A new instance of this type, populated with json
        """
        make_cls = CLASS_MAP.get(id) # in this case, ID is coming in as the type

        if make_cls is None:
            # we don't recognize this entity type - do nothing?
            return None

        # discard the envelope
        real_json = json['data']
        real_id = real_json['id']

        # make the real object type
        return Base.make(real_id, client, make_cls, parent_id=None, json=real_json)

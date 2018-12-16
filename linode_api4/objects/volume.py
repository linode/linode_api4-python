from __future__ import absolute_import

from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects import Base, Instance, Property, Region


class Volume(Base):
    api_endpoint = '/volumes/{id}'

    properties = {
        'id': Property(identifier=True),
        'created': Property(is_datetime=True),
        'updated': Property(is_datetime=True),
        'linode_id': Property(id_relationship=Instance),
        'label': Property(mutable=True, filterable=True),
        'size': Property(filterable=True),
        'status': Property(filterable=True),
        'region': Property(slug_relationship=Region),
        'tags': Property(mutable=True),
    }

    def attach(self, to_linode, config=None):
        """
        Attaches this Volume to the given Linode
        """
        result = self._client.post('{}/attach'.format(Volume.api_endpoint), model=self,
                data={
                    "linode_id": to_linode.id if issubclass(type(to_linode), Base) else to_linode,
                    "config": None if not config else config.id if issubclass(type(config), Base) else config,
        })

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when attaching volume!', json=result)

        self._populate(result)
        return True

    def detach(self):
        """
        Detaches this Volume if it is attached
        """
        self._client.post('{}/detach'.format(Volume.api_endpoint), model=self)

        return True

    def resize(self, size):
        """
        Resizes this Volume
        """
        result = self._client.post('{}/resize'.format(Volume.api_endpoint, model=self,
            data={ "size": size }))

        self._populate(result.json)

        return True

    def clone(self, label):
        """
        Clones this volume to a new volume in the same region with the given label

        :param label: The label for the new volume.

        :returns: The new volume object.
        """
        result = self._client.post('{}/clone'.format(Volume.api_endpoint),
                model=self, data={'label': label})

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response cloning volume!')

        return Volume(self._client, result['id'], result)

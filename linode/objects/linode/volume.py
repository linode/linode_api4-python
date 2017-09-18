from ...errors import UnexpectedResponseError
from .. import Base, Property, Region
from . import Linode

class Volume(Base):
    api_endpoint = '/linode/volumes/{id}'

    properties = {
        'id': Property(identifier=True),
        'created': Property(is_datetime=True),
        'updated': Property(is_datetime=True),
        'linode_id': Property(id_relationship=Linode),
        'label': Property(mutable=True, filterable=True),
        'size': Property(filterable=True),
        'status': Property(filterable=True),
        'region': Property(slug_relationship=Region),
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
            raise UnexpectedResponseErorr('Unexpected response when attaching volume!', json=result)

        self._populate(result)
        return True

    def detach(self):
        """
        Detaches this Volume if it is attached
        """
        result = self._client.post('{}/detach'.format(Volume.api_endpoint), model=self)

        return True

    def resize(self, size):
        """
        Resizes this Volume
        """
        result = self._client.post('{}/resize'.format(Volume.api_endpoint, model=self,
            data={ "size": size }))

        self._populate(result.json)

        return True

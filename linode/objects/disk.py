from .base import Base, Property

class Disk(Base):
    api_endpoint = '/linodes/{linode_id}/disks/{id}'
    properties = {
        'id': Property(identifier=True),
        'created': Property(),
        'label': Property(mutable=True),
        'size': Property(),
        'status': Property(),
        'type': Property(),
        'updated': Property(),
    }

    def __init__(self, linode_id, id):
        Base.__init__(self)

        self._set('id', id)
        self._set('linode_id' ,linode_id)

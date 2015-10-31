from .base import Base 

class Disk(Base):
    api_endpoint = '/linodes/{linode_id}/disks/{id}'
    properties = ('id', 'created', 'label', 'size', 'status', 'type', 'updated')

    def __init__(self, linode_id, id):
        Base.__init__(self)

        self.id = id
        self.linode_id = linode_id

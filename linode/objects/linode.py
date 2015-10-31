from .base import Base

class Linode(Base): 
    api_endpoint = '/linodes/{id}'
    properties = ('id', 'label', 'group', 'status', 'created', 'updated', 'total_transfer', 
        'ip_addresses', 'distribution', 'host', 'alerts', 'ssh_command', 'lish_command', )

    def __init__(self, id):
        Base.__init__(self)

        self.id = id


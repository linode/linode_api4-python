from .base import Base
from linode.api import api_call

class Linode(Base): 
    api_endpoint = '/linodes/{id}'
    properties = ('id', 'label', 'group', 'status', 'created', 'updated', 'total_transfer', 
        'ip_addresses', 'distribution', 'host', 'alerts', 'ssh_command', 'lish_command', )

    def __init__(self, id):
        Base.__init__(self)

        self.id = id

    def boot(self, config=None):
        # TODO: Implement configs
        resp = api_call("{}/boot".format(Linode.api_endpoint), model=self, method="POST")

        if 'error' in resp:
            return False
        return True

    def shutdown(self):
        resp = api_call("{}/shutdown".format(Linode.api_endpoint), model=self, method="POST")

        if 'error' in resp:
            return False
        return True

    def reboot(self):
        resp = api_call("{}/reboot".format(Linode.api_endpoint), model=self, method="POST")

        if 'error' in resp:
            return False
        return True

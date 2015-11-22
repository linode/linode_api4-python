from .base import Base, Property
from .disk import Disk
from linode.api import api_call

class Linode(Base): 
    api_endpoint = '/linodes/{id}'
    properties = {
        'id': Property(identifier=True),
        'label': Property(mutable=True),
        'group': Property(mutable=True),
        'status': Property(volatile=True),
        'created': Property(is_datetime=True),
        'updated': Property(volatile=True, is_datetime=True),
        'total_transfer': Property(),
        'ip_addresses': Property(),
        'distribution': Property(),
        'datacenter': Property(relationship=True),
        'alerts': Property(),
        'ssh_command': Property(),
        'lish_command': Property(),
        'distribution': Property(relationship=True),
        'disks': Property(derived_class=Disk),
        #'configs': Property(derived_class=Config),
    }

    def __init__(self, id):
        Base.__init__(self)

        self._set('id', id)

    def __repr__(self):
        return "Linode: {}".format(self.id)

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

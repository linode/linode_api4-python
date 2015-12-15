from .base import Base, Property
from .disk import Disk
from .config import Config
from .job import Job
from linode.api import api_call

from random import choice

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
        'configs': Property(derived_class=Config),
        'jobs': Property(derived_class=Job),
    }

    def __init__(self, id):
        Base.__init__(self)

        self._set('id', id)

    def __repr__(self):
        return "Linode: {}".format(self.id)

    def boot(self, config=None):
        resp = api_call("{}/boot".format(Linode.api_endpoint), model=self, method="POST", data={'config': config.id} if config else 'junk')

        if 'error' in resp:
            return False
        return True

    def shutdown(self):
        resp = api_call("{}/shutdown".format(Linode.api_endpoint), model=self, method="POST")

        if 'error' in resp:
            return False
        return True

    def reboot(self):
        resp = api_call("{}/reboot".format(Linode.api_endpoint), model=self, method="POST", data="junk")

        if 'error' in resp:
            return False
        return True

    def deploy_distro(self, distro, root_pass=None, root_key=None, swap_size=None, label=None,
            stackscript=None, **stackscript_args):
        """
        Deploy a distro to a linode.  If not root password is provided, one will be generated
        and returned with the result.  If a stackscript is provided, any other keyword arguments
        provided will be passed as stackscript parameters.
        """
        params = {
            "distribution": distro.id,
        }

        gen_pass = ''
        if root_pass:
            params['root_pass'] = root_pass
        else:
            params['root_pass'] = Linode.generate_root_password()

        if root_key:
            params['root_key'] = root_key
        if swap_size:
            params['swap_size'] = swap_size
        if label:
            params['label'] = label
        if stackscript:
            params['stackscript'] = stackscript.id
            if stackscript_args:
                params['stackscript_data'] = stackscript_args

        result = api_call('/linodes/{}/deploy'.format(self.id), method='POST', data=params)

        #TODO: handle errors
        self._populate(result['linode'])
        if root_pass:
            return self
        else:
            return self, gen_pass

    def generate_root_password():
        return ''.join([choice('abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*_+-=') for _ in range(0, 32) ])

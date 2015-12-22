from .base import Base, Property
from .disk import Disk
from .config import Config
from .job import Job

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

    def boot(self, config=None):
        resp = self._client.post("{}/boot".format(Linode.api_endpoint), model=self, data={'config': config.id} if config else None)

        if 'error' in resp:
            return False
        return True

    def shutdown(self):
        resp = self._client.post("{}/shutdown".format(Linode.api_endpoint), model=self)

        if 'error' in resp:
            return False
        return True

    def reboot(self):
        resp = self._client.post("{}/reboot".format(Linode.api_endpoint), model=self)

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

        result = self._client.post('/linodes/{}/deploy'.format(self.id), data=params)

        #TODO: handle errors
        self._populate(result['linode'])
        if root_pass:
            return self
        else:
            return self, gen_pass

    def generate_root_password():
        return ''.join([choice('abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*_+-=') for _ in range(0, 32) ])


    def create_config(self, kernel, label=None, disks=None, **kwargs):

        disk_list = []
        if disks:
            disk_list = [ d.id for d in disks ]

        params = {
            'kernel': kernel.id,
            'label': label if label else "{}_config_{}".format(self.label, len(self.configs)),
            'disk_list': disk_list,
        }
        params.update(kwargs)

        result = self._client.post("{}/configs".format(Linode.api_endpoint), model=self, data=params)
        self.invalidate()

        if not 'config' in result:
            return result

        c = Config(self._client, result['config']['id'], self.id)
        c._populate(result['config'])
        return c

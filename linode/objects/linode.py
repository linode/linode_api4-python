from .base import Base, Property
from .disk import Disk
from .config import Config

from random import choice

class Linode(Base):
    api_endpoint = '/linodes/{id}'
    properties = {
        'id': Property(identifier=True),
        'label': Property(mutable=True, filterable=True),
        'group': Property(mutable=True, filterable=True),
        'state': Property(volatile=True),
        'created': Property(is_datetime=True),
        'updated': Property(volatile=True, is_datetime=True),
        'total_transfer': Property(),
        'ip_addresses': Property(),
        'distribution': Property(),
        'datacenter': Property(relationship=True, filterable=True),
        'alerts': Property(),
        'distribution': Property(relationship=True, filterable=True),
        'disks': Property(derived_class=Disk),
        'configs': Property(derived_class=Config),
        'services': Property(relationship=True),
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

    @staticmethod
    def generate_root_password():
        return ''.join([choice('abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*_+-=') for _ in range(0, 32) ])

    # create derived objects
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

    def create_disk(self, size, label=None, filesystem=None, read_only=False, distribution=None, \
            root_pass=None, root_key=None, stackscript=None, **stackscript_args):

        gen_pass = None
        if distribution and not root_pass:
            gen_pass  = Linode.generate_root_password()
            root_pass = gen_pass


        if distribution and not label:
            label = "My {} Disk".format(distribution.label)

        params = {
            'size': size,
            'label': label if label else "{}_disk_{}".format(self.label, len(self.disks)),
            'read_only': read_only,
            'filesystem': filesystem if filesystem else 'raw',
        }

        if distribution:
            params.update({
                'distribution': distribution.id,
                'root_pass': root_pass,
            })

        if stackscript:
            params['stackscript'] = stackscript.id
            if stackscript_args:
                params['stackscript_data'] = stackscript_args

        result = self._client.post("{}/disks".format(Linode.api_endpoint), model=self, data=params)
        self.invalidate()

        if not 'disk' in result:
            return result

        d = Disk(self._client, result['disk']['id'], self.id)
        d._populate(result['disk'])

        if gen_pass:
            return d, gen_pass
        return d

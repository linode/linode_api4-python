from __future__ import absolute_import

from datetime import datetime
import string
from random import choice

from linode.common import load_and_validate_keys
from linode.errors import UnexpectedResponseError
from linode.objects import Base, Image, Property, Region
from linode.objects.base import MappedObject
from linode.objects.networking import IPAddress, IPv6Pool
from linode.paginated_list import PaginatedList

from .backup import Backup
from .config import Config
from .disk import Disk
from .linode_type import Type


class Linode(Base):
    api_endpoint = '/linode/instances/{id}'
    properties = {
        'id': Property(identifier=True),
        'label': Property(mutable=True, filterable=True),
        'group': Property(mutable=True, filterable=True),
        'status': Property(volatile=True),
        'created': Property(is_datetime=True),
        'updated': Property(volatile=True, is_datetime=True),
        'region': Property(slug_relationship=Region, filterable=True),
        'alerts': Property(),
        'image': Property(slug_relationship=Image, filterable=True),
        'disks': Property(derived_class=Disk),
        'configs': Property(derived_class=Config),
        'type': Property(slug_relationship=Type),
        'backups': Property(),
        'ipv4': Property(),
        'ipv6': Property(),
        'hypervisor': Property(),
        'specs': Property(),
    }

    @property
    def ips(self):
        """
        The ips related collection is not normalized like the others, so we have to
        make an ad-hoc object to return for its response
        """
        if not hasattr(self, '_ips'):
            result = self._client.get("{}/ips".format(Linode.api_endpoint), model=self)

            if not "ipv4" in result:
                raise UnexpectedResponseError('Unexpected response loading IPs', json=result)

            v4pub = []
            for c in result['ipv4']['public']:
                i = IPAddress(self._client, c['address'], c)
                v4pub.append(i)

            v4pri = []
            for c in result['ipv4']['private']:
                i = IPAddress(self._client, c['address'], c)
                v4pri.append(i)

            shared_ips = []
            for c in result['ipv4']['shared']:
                i = IPAddress(self._client, c['address'], c)
                shared_ips.append(i)

            v6 = []
            for c in result['ipv6']['addresses']:
                i = IPAddress(self._client, c['address'], c)
                v6.append(i)

            slaac = IPAddress(self._client, result['ipv6']['slaac']['address'],
                              result['ipv6']['slaac'])
            link_local = IPAddress(self._client, result['ipv6']['link_local']['address'],
                                   result['ipv6']['link_local'])

            pools = []
            for p in result['ipv6']['global']:
                pools.append(IPv6Pool(self._client, p['range']))

            ips = MappedObject(**{
                "ipv4": {
                    "public": v4pub,
                    "private": v4pri,
                    "shared": shared_ips,
                },
                "ipv6": {
                    "slaac": slaac,
                    "link_local": link_local,
                    "pools": pools,
                    "addresses": v6,
                },
            })

            self._set('_ips', ips)

        return self._ips

    @property
    def available_backups(self):
        """
        The backups response contains what backups are available to be restored.
        """
        if not hasattr(self, '_avail_backups'):
            result = self._client.get("{}/backups".format(Linode.api_endpoint), model=self)

            if not 'automatic' in result:
                raise UnexpectedResponseError('Unexpected response loading available backups!', json=result)

            automatic = []
            for a in result['automatic']:
                cur = Backup(self._client, a['id'], self.id, a)
                automatic.append(cur)

            snap = None
            if result['snapshot']['current']:
                snap = Backup(self._client, result['snapshot']['current']['id'], self.id,
                        result['snapshot']['current'])

            psnap = None
            if result['snapshot']['in_progress']:
                psnap = Backup(self._client, result['snapshot']['in_progress']['id'], self.id,
                        result['snapshot']['in_progress'])

            self._set('_avail_backups', MappedObject(**{
                "automatic": automatic,
                "snapshot": {
                    "current": snap,
                    "in_progress": psnap,
                }
            }))

        return self._avail_backups

    def _populate(self, json):
        if json is not None:
            # fixes ipv4 and ipv6 attribute of json to make base._populate work
            if 'ipv4' in json and 'address' in json['ipv4']:
                json['ipv4']['id'] = json['ipv4']['address']
            if 'ipv6' in json and isinstance(json['ipv6'], list):
                for j in json['ipv6']:
                    j['id'] = j['range']

        Base._populate(self, json)

    def invalidate(self):
        """ Clear out cached properties """
        if hasattr(self, '_avail_backups'):
            del self._avail_backups
        if hasattr(self, '_ips'):
            del self._ips

        Base.invalidate(self)

    def boot(self, config=None):
        resp = self._client.post("{}/boot".format(Linode.api_endpoint), model=self, data={'config_id': config.id} if config else None)

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
    def create_config(self, kernel=None, label=None, devices=[], disks=[],
            volumes=[], **kwargs):
        """
        Creates a Linode Config with the given attributes.

        :param kernel: The kernel to boot with.
        :param label: The config label
        :param disks: The list of disks, starting at sda, to map to this config.
        :param volumes: The volumes, starting after the last disk, to map to this
            config
        :param devices: A list of devices to assign to this config, in device
            index order.  Values must be of type Disk or Volume. If this is
            given, you may not include disks or volumes.
        :param **kwargs: Any other arguments accepted by the api.

        :returns: A new Linode Config
        """
        from ..volume import Volume

        hypervisor_prefix = 'sd' if self.hypervisor == 'kvm' else 'xvd'
        device_names = [hypervisor_prefix + string.ascii_lowercase[i] for i in range(0, 8)]
        device_map = {device_names[i]: None for i in range(0, len(device_names))}

        if devices and (disks or volumes):
            raise ValueError('You may not call create_config with "devices" and '
                    'either of "disks" or "volumes" specified!')

        if not devices:
            if not isinstance(disks, list):
                disks = [disks]
            if not isinstance(volumes, list):
                volumes = [volumes]

            devices = []

            for d in disks:
                if d is None:
                    devices.append(None)
                elif isinstance(d, Disk):
                    devices.append(d)
                else:
                    devices.append(Disk(self._client, int(d), self.id))

            for v in volumes:
                if v is None:
                    devices.append(None)
                elif isinstance(v, Volume):
                    devices.append(v)
                else:
                    devices.append(Volume(self._client, int(v)))

        if not devices:
            raise ValueError('Must include at least one disk or volume!')

        for i, d in enumerate(devices):
            if d is None:
                pass
            elif isinstance(d, Disk):
                device_map[device_names[i]] = {'disk_id': d.id }
            elif isinstance(d, Volume):
                device_map[device_names[i]] = {'volume_id': d.id }
            else:
                raise TypeError('Disk or Volume expected!')

        params = {
            'kernel': kernel.id if issubclass(type(kernel), Base) else kernel,
            'label': label if label else "{}_config_{}".format(self.label, len(self.configs)),
            'devices': device_map,
        }
        params.update(kwargs)

        result = self._client.post("{}/configs".format(Linode.api_endpoint), model=self, data=params)
        self.invalidate()

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response creating config!', json=result)

        c = Config(self._client, result['id'], self.id, result)
        return c

    def create_disk(self, size, label=None, filesystem=None, read_only=False, image=None,
            root_pass=None, authorized_keys=None, stackscript=None, **stackscript_args):

        gen_pass = None
        if image and not root_pass:
            gen_pass  = Linode.generate_root_password()
            root_pass = gen_pass

        authorized_keys = load_and_validate_keys(authorized_keys)

        if image and not label:
            label = "My {} Disk".format(image.label)

        params = {
            'size': size,
            'label': label if label else "{}_disk_{}".format(self.label, len(self.disks)),
            'read_only': read_only,
            'filesystem': filesystem if filesystem else 'raw',
            'authorized_keys': authorized_keys,
        }

        if image:
            params.update({
                'image': image.id if issubclass(type(image), Base) else image,
                'root_pass': root_pass,
            })

        if stackscript:
            params['stackscript_id'] = stackscript.id
            if stackscript_args:
                params['stackscript_data'] = stackscript_args

        result = self._client.post("{}/disks".format(Linode.api_endpoint), model=self, data=params)
        self.invalidate()

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response creating disk!', json=result)

        d = Disk(self._client, result['id'], self.id, result)

        if gen_pass:
            return d, gen_pass
        return d

    def enable_backups(self):
        result = self._client.post("{}/backups/enable".format(Linode.api_endpoint), model=self)
        self._populate(result)
        return True

    def cancel_backups(self):
        result = self._client.post("{}/backups/cancel".format(Linode.api_endpoint), model=self)
        self._populate(result)
        return True

    def snapshot(self, label=None):
        result = self._client.post("{}/backups".format(Linode.api_endpoint), model=self,
            data={ "label": label })

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response taking snapshot!', json=result)

        # so the changes show up the next time they're accessed
        if hasattr(self, '_avail_backups'):
            del self._avail_backups

        b = Backup(self._client, result['id'], self.id, result)
        return b

    def allocate_ip(self, public=False):
        result = self._client.post("{}/ips".format(Linode.api_endpoint), model=self,
                data={ "type": "public" if public else "private" })

        if not 'address' in result:
            raise UnexpectedResponseError('Unexpected response allocating IP!', json=result)

        i = IPAddress(self._client, result['address'], result)
        return i

    def rebuild(self, image, root_pass=None, authorized_keys=None, **kwargs):
        ret_pass = None
        if not root_pass:
            ret_pass = Linode.generate_root_password()
            root_pass = ret_pass

        authorized_keys = load_and_validate_keys(authorized_keys)

        params = {
             'image': image.id if issubclass(type(image), Base) else image,
             'root_pass': root_pass,
             'authorized_keys': authorized_keys,
         }
        params.update(kwargs)

        result = self._client.post('{}/rebuild'.format(Linode.api_endpoint), model=self, data=params)

        if not 'disks' in result:
            raise UnexpectedResponseError('Unexpected response issuing rebuild!', json=result)

        self.invalidate()
        if not ret_pass:
            return True
        else:
            return ret_pass

    def rescue(self, *disks):
        if disks:
            disks = { x: { 'disk_id': y } for x,y in zip(('sda','sdb'), disks) }
        else:
            disks=None

        result = self._client.post('{}/rescue'.format(Linode.api_endpoint), model=self,
                data={ "devices": disks })

        return result

    def set_shared_ips(self, *ips):
        """
        Takes a list of IP Addresses (either objects or strings) and attempts to
        set them as the Shared IPs for this Linode
        """
        params = []
        for ip in ips:
            if isinstance(ip, str):
                params.append(ip)
            elif isinstance(ip, IPAddress):
                params.append(ip.address)
            else:
                params.append(str(ip)) # and hope that works

        params = {
            "ips": params
        }

        self._client.post('{}/ips/sharing'.format(Linode.api_endpoint), model=self,
                data=params)

        # so the changes show up next time they're accessed
        if hasattr(self, '_ips'):
            del self._ips

        return True

    def kvmify(self):
        """
        Converts this linode to KVM from Xen
        """
        self._client.post('{}/kvmify'.format(Linode.api_endpoint), model=self)

        return True

    def mutate(self):
        """
        Upgrades this Linode to the latest generation type
        """
        self._client.post('{}/mutate'.format(Linode.api_endpoint), model=self)

        return True

    def clone(self, to_linode=None, region=None, service=None, configs=[], disks=[],
            label=None, group=None, with_backups=None):
        """ Clones this linode into a new linode or into a new linode in the given region """
        if to_linode and region:
            raise ValueError('You may only specify one of "to_linode" and "region"')

        if region and not service:
            raise ValueError('Specifying a region requires a "service" as well')

        if not isinstance(configs, list) and not isinstance(configs, PaginatedList):
            configs = [configs]
        if not isinstance(disks, list) and not isinstance(disks, PaginatedList):
            disks = [disks]

        cids = [ c.id if issubclass(type(c), Base) else c for c in configs ]
        dids = [ d.id if issubclass(type(d), Base) else d for d in disks ]

        params = {
            "linode_id": to_linode.id if issubclass(type(to_linode), Base) else to_linode,
            "region": region.id if issubclass(type(region), Base) else region,
            "type": service.id if issubclass(type(service), Base) else service,
            "configs": cids if cids else None,
            "disks": dids if dids else None,
            "label": label,
            "group": group,
            "with_backups": with_backups,
        }

        result = self._client.post('{}/clone'.format(Linode.api_endpoint), model=self, data=params)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response cloning Linode!', json=result)

        l = Linode(self._client, result['id'], result)
        return l

    @property
    def stats(self):
        """
        Returns the JSON stats for this Linode
        """
        # TODO - this would be nicer if we formatted the stats
        return self._client.get('{}/stats'.format(Linode.api_endpoint), model=self)

    def stats_for(self, dt):
        """
        Returns stats for the month containing the given datetime
        """
        # TODO - this would be nicer if we formatted the stats
        if not isinstance(dt, datetime):
            raise TypeError('stats_for requires a datetime object!')
        return self._client.get('{}/stats/'.format(dt.strftime('%Y/%m')))

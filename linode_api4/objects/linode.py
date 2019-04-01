from __future__ import absolute_import

import string
import sys
from datetime import datetime
from enum import Enum
from os import urandom
from random import randint

from linode_api4.common import load_and_validate_keys
from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects import Base, DerivedBase, Image, Property, Region
from linode_api4.objects.base import MappedObject
from linode_api4.objects.filtering import FilterableAttribute
from linode_api4.objects.networking import IPAddress, IPv6Pool
from linode_api4.paginated_list import PaginatedList

PASSWORD_CHARS = string.ascii_letters + string.digits + string.punctuation


class Backup(DerivedBase):
    api_endpoint = '/linode/instances/{linode_id}/backups/{id}'
    derived_url_path = 'backups'
    parent_id_name='linode_id'

    properties = {
        'id': Property(identifier=True),
        'created': Property(is_datetime=True),
        'duration': Property(),
        'updated': Property(is_datetime=True),
        'finished': Property(is_datetime=True),
        'message': Property(),
        'status': Property(volatile=True),
        'type': Property(),
        'linode_id': Property(identifier=True),
        'label': Property(),
        'configs': Property(),
        'disks': Property(),
        'region': Property(slug_relationship=Region),
    }

    def restore_to(self, linode, **kwargs):
        d = {
            "linode_id": linode.id if issubclass(type(linode), Base) else linode,
        }
        d.update(kwargs)

        self._client.post("{}/restore".format(Backup.api_endpoint), model=self,
            data=d)
        return True


class Disk(DerivedBase):
    api_endpoint = '/linode/instances/{linode_id}/disks/{id}'
    derived_url_path = 'disks'
    parent_id_name='linode_id'

    properties = {
        'id': Property(identifier=True),
        'created': Property(is_datetime=True),
        'label': Property(mutable=True, filterable=True),
        'size': Property(filterable=True),
        'status': Property(filterable=True, volatile=True),
        'filesystem': Property(),
        'updated': Property(is_datetime=True),
        'linode_id': Property(identifier=True),
    }


    def duplicate(self):
        result = self._client.post(Disk.api_endpoint, model=self, data={})

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response duplicating disk!', json=result)

        d = Disk(self._client, result['id'], self.linode_id, result)
        return d


    def reset_root_password(self, root_password=None):
        rpass = root_password
        if not rpass:
            rpass = Instance.generate_root_password()

        params = {
            'password': rpass,
        }

        result = self._client.post(Disk.api_endpoint, model=self, data=params)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response duplicating disk!', json=result)

        self._populate(result)
        if not root_password:
            return True, rpass
        return True

    def resize(self, new_size):
        """
        Resizes this disk.  The Linode Instance this disk belongs to must have
        sufficient space available to accommodate the new size, and must be
        offline.

        **NOTE** If resizing a disk down, the filesystem on the disk must still
        fit on the new disk size.  You may need to resize the filesystem on the
        disk first before performing this action.

        :param new_size: The intended new size of the disk, in MB
        :type new_size: int

        :returns: True if the resize was initiated successfully.
        :rtype: bool
        """
        self._client.post('{}/resize'.format(Disk.api_endpoint), model=self, data={"size": new_size})

        return True


class Kernel(Base):
    api_endpoint="/linode/kernels/{id}"
    properties = {
        "created": Property(is_datetime=True),
        "deprecated": Property(filterable=True),
        "description": Property(),
        "id": Property(identifier=True),
        "kvm": Property(filterable=True),
        "label": Property(filterable=True),
        "updates": Property(),
        "version": Property(filterable=True),
        "architecture": Property(filterable=True),
        "xen": Property(filterable=True),
    }


class Type(Base):
    api_endpoint = "/linode/types/{id}"
    properties = {
        'disk': Property(filterable=True),
        'id': Property(identifier=True),
        'label': Property(filterable=True),
        'network_out': Property(filterable=True),
        'price': Property(),
        'addons': Property(),
        'memory': Property(filterable=True),
        'transfer': Property(filterable=True),
        'vcpus': Property(filterable=True),
        # type_class is populated from the 'class' attribute of the returned JSON
    }

    def _populate(self, json):
        """
        Allows changing the name "class" in JSON to "type_class" in python
        """
        super(Type, self)._populate(json)

        if 'class' in json:
            setattr(self, 'type_class', json['class'])
        else:
            setattr(self, 'type_class', None)

    # allow filtering on this converted type
    type_class = FilterableAttribute('class')


class Config(DerivedBase):
    api_endpoint="/linode/instances/{linode_id}/configs/{id}"
    derived_url_path="configs"
    parent_id_name="linode_id"

    properties = {
        "id": Property(identifier=True),
        "linode_id": Property(identifier=True),
        "helpers": Property(),#TODO: mutable=True),
        "created": Property(is_datetime=True),
        "root_device": Property(mutable=True),
        "kernel": Property(relationship=Kernel, mutable=True, filterable=True),
        "devices": Property(filterable=True),#TODO: mutable=True),
        "initrd": Property(relationship=Disk),
        "updated": Property(),
        "comments": Property(mutable=True, filterable=True),
        "label": Property(mutable=True, filterable=True),
        "run_level": Property(mutable=True, filterable=True),
        "virt_mode": Property(mutable=True, filterable=True),
        "memory_limit": Property(mutable=True, filterable=True),
    }

    def _populate(self, json):
        """
        Map devices more nicely while populating.
        """
        from .volume import Volume

        DerivedBase._populate(self, json)

        devices = {}
        for device_index, device in json['devices'].items():
            if not device:
                devices[device_index] = None
                continue

            dev = None
            if 'disk_id' in device and device['disk_id']: # this is a disk
                dev = Disk.make_instance(device['disk_id'], self._client,
                        parent_id=self.linode_id)
            else:
                dev = Volume.make_instance(device['volume_id'], self._client,
                        parent_id=self.linode_id)
            devices[device_index] = dev

        self._set('devices', MappedObject(**devices))


class Instance(Base):
    api_endpoint = '/linode/instances/{id}'
    properties = {
        'id': Property(identifier=True, filterable=True),
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
        'tags': Property(mutable=True),
    }

    @property
    def ips(self):
        """
        The ips related collection is not normalized like the others, so we have to
        make an ad-hoc object to return for its response
        """
        if not hasattr(self, '_ips'):
            result = self._client.get("{}/ips".format(Instance.api_endpoint), model=self)

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
            result = self._client.get("{}/backups".format(Instance.api_endpoint), model=self)

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
        resp = self._client.post("{}/boot".format(Instance.api_endpoint), model=self, data={'config_id': config.id} if config else None)

        if 'error' in resp:
            return False
        return True

    def shutdown(self):
        resp = self._client.post("{}/shutdown".format(Instance.api_endpoint), model=self)

        if 'error' in resp:
            return False
        return True

    def reboot(self):
        resp = self._client.post("{}/reboot".format(Instance.api_endpoint), model=self)

        if 'error' in resp:
            return False
        return True

    def resize(self, new_type):
        new_type = new_type.id if issubclass(type(new_type), Base) else new_type
        resp = self._client.post("{}/resize".format(Instance.api_endpoint), model=self, data={"type": new_type})

        if 'error' in resp:
            return False
        return True

    @staticmethod
    def generate_root_password():
        def _func(value):
            if sys.version_info[0] < 3:
                value = int(value.encode('hex'), 16)
            return value

        password = ''.join([
            PASSWORD_CHARS[_func(c) % len(PASSWORD_CHARS)]
            for c in urandom(randint(50, 110))
        ])

        # ensure the generated password is not too long
        if len(password) > 110:
            password = password[:110]

        return password

    # create derived objects
    def config_create(self, kernel=None, label=None, devices=[], disks=[],
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
        from .volume import Volume

        hypervisor_prefix = 'sd' if self.hypervisor == 'kvm' else 'xvd'
        device_names = [hypervisor_prefix + string.ascii_lowercase[i] for i in range(0, 8)]
        device_map = {device_names[i]: None for i in range(0, len(device_names))}

        if devices and (disks or volumes):
            raise ValueError('You may not call config_create with "devices" and '
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

        result = self._client.post("{}/configs".format(Instance.api_endpoint), model=self, data=params)
        self.invalidate()

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response creating config!', json=result)

        c = Config(self._client, result['id'], self.id, result)
        return c

    def disk_create(self, size, label=None, filesystem=None, read_only=False, image=None,
            root_pass=None, authorized_keys=None, stackscript=None, **stackscript_args):

        gen_pass = None
        if image and not root_pass:
            gen_pass  = Instance.generate_root_password()
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

        result = self._client.post("{}/disks".format(Instance.api_endpoint), model=self, data=params)
        self.invalidate()

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response creating disk!', json=result)

        d = Disk(self._client, result['id'], self.id, result)

        if gen_pass:
            return d, gen_pass
        return d

    def enable_backups(self):
        """
        Enable Backups for this Instance.  When enabled, we will automatically
        backup your Instance's data so that it can be restored at a later date.
        For more information on Instance's Backups service and pricing, see our
        `Backups Page`_

        .. _Backups Page: https://www.linode.com/backups
        """
        self._client.post("{}/backups/enable".format(Instance.api_endpoint), model=self)
        self.invalidate()
        return True

    def cancel_backups(self):
        """
        Cancels Backups for this Instance.  All existing Backups will be lost,
        including any snapshots that have been taken.  This cannot be undone,
        but Backups can be re-enabled at a later date.
        """
        self._client.post("{}/backups/cancel".format(Instance.api_endpoint), model=self)
        self.invalidate()
        return True

    def snapshot(self, label=None):
        result = self._client.post("{}/backups".format(Instance.api_endpoint), model=self,
                                   data={ "label": label })

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response taking snapshot!', json=result)

        # so the changes show up the next time they're accessed
        if hasattr(self, '_avail_backups'):
            del self._avail_backups

        b = Backup(self._client, result['id'], self.id, result)
        return b

    def ip_allocate(self, public=False):
        """
        Allocates a new :any:`IPAddress` for this Instance.  Additional public
        IPs require justification, and you may need to open a :any:`SupportTicket`
        before you can add one.  You may only have, at most, one private IP per
        Instance.

        :param public: If the new IP should be public or private.  Defaults to
                       private.
        :type public: bool

        :returns: The new IPAddress
        :rtype: IPAddress
        """
        result = self._client.post(
            "{}/ips".format(Instance.api_endpoint),
            model=self,
            data={
                "type": "ipv4",
                "public": public,
            })

        if not 'address' in result:
            raise UnexpectedResponseError('Unexpected response allocating IP!',
                                          json=result)

        i = IPAddress(self._client, result['address'], result)
        return i

    def rebuild(self, image, root_pass=None, authorized_keys=None, **kwargs):
        """
        Rebuilding an Instance deletes all existing Disks and Configs and deploys
        a new :any:`Image` to it.  This can be used to reset an existing
        Instance or to install an Image on an empty Instance.

        :param image: The Image to deploy to this Instance
        :type image: str or Image
        :param root_pass: The root password for the newly rebuilt Instance.  If
                          omitted, a password will be generated and returned.
        :type root_pass: str
        :param authorized_keys: The ssh public keys to install in the linode's
                                /root/.ssh/authorized_keys file.  Each entry may
                                be a single key, or a path to a file containing
                                the key.
        :type authorized_keys: list or str

        :returns: The newly generated password, if one was not provided
                  (otherwise True)
        :rtype: str or bool
        """
        ret_pass = None
        if not root_pass:
            ret_pass = Instance.generate_root_password()
            root_pass = ret_pass

        authorized_keys = load_and_validate_keys(authorized_keys)

        params = {
             'image': image.id if issubclass(type(image), Base) else image,
             'root_pass': root_pass,
             'authorized_keys': authorized_keys,
         }
        params.update(kwargs)

        result = self._client.post('{}/rebuild'.format(Instance.api_endpoint), model=self, data=params)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response issuing rebuild!', json=result)

        # update ourself with the newly-returned information
        self._populate(result)

        if not ret_pass:
            return True
        else:
            return ret_pass

    def rescue(self, *disks):
        if disks:
            disks = { x: { 'disk_id': y } for x,y in zip(('sda','sdb','sdc','sdd','sde','sdf','sdg'), disks) }
        else:
            disks=None

        result = self._client.post('{}/rescue'.format(Instance.api_endpoint), model=self,
                                   data={ "devices": disks })

        return result

    def kvmify(self):
        """
        Converts this linode to KVM from Xen
        """
        self._client.post('{}/kvmify'.format(Instance.api_endpoint), model=self)

        return True

    def mutate(self):
        """
        Upgrades this Instance to the latest generation type
        """
        self._client.post('{}/mutate'.format(Instance.api_endpoint), model=self)

        return True

    def initiate_migration(self):
        """
        Initiates a pending migration that is already scheduled for this Linode
        Instance
        """
        self._client.post('{}/migrate'.format(Instance.api_endpoint), model=self)

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

        result = self._client.post('{}/clone'.format(Instance.api_endpoint), model=self, data=params)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response cloning Instance!', json=result)

        l = Instance(self._client, result['id'], result)
        return l

    @property
    def stats(self):
        """
        Returns the JSON stats for this Instance
        """
        # TODO - this would be nicer if we formatted the stats
        return self._client.get('{}/stats'.format(Instance.api_endpoint), model=self)

    def stats_for(self, dt):
        """
        Returns stats for the month containing the given datetime
        """
        # TODO - this would be nicer if we formatted the stats
        if not isinstance(dt, datetime):
            raise TypeError('stats_for requires a datetime object!')
        return self._client.get('{}/stats/'.format(dt.strftime('%Y/%m')))


class UserDefinedFieldType(Enum):
    text = 1
    select_one = 2
    select_many = 3

class UserDefinedField():
    def __init__(self, name, label, example, field_type, choices=None):
        self.name = name
        self.label = label
        self.example = example
        self.field_type = field_type
        self.choices = choices

    def __repr__(self):
        return "{}({}): {}".format(self.label, self.field_type.name, self.example)

class StackScript(Base):
    api_endpoint = '/linode/stackscripts/{id}'
    properties = {
        "user_defined_fields": Property(),
        "label": Property(mutable=True, filterable=True),
        "rev_note": Property(mutable=True),
        "username": Property(filterable=True),
        "user_gravatar_id": Property(),
        "is_public": Property(mutable=True, filterable=True),
        "created": Property(is_datetime=True),
        "deployments_active": Property(),
        "script": Property(mutable=True),
        "images": Property(mutable=True, filterable=True), # TODO make slug_relationship
        "deployments_total": Property(),
        "description": Property(mutable=True, filterable=True),
        "updated": Property(is_datetime=True),
    }

    def _populate(self, json):
        """
        Override the populate method to map user_defined_fields to
        fancy values
        """
        Base._populate(self, json)

        mapped_udfs = []
        for udf in self.user_defined_fields:
            t = UserDefinedFieldType.text
            choices = None
            if hasattr(udf, 'oneof'):
                t = UserDefinedFieldType.select_one
                choices = udf.oneof.split(',')
            elif hasattr(udf, 'manyof'):
                t = UserDefinedFieldType.select_many
                choices = udf.manyof.split(',')

            mapped_udfs.append(UserDefinedField(udf.name,
                    udf.label if hasattr(udf, 'label') else None,
                    udf.example if hasattr(udf, 'example') else None,
                    t, choices=choices))

        self._set('user_defined_fields', mapped_udfs)
        ndist = [ Image(self._client, d) for d in self.images ]
        self._set('images', ndist)

    def _serialize(self):
        dct = Base._serialize(self)
        dct['images'] = [ d.id for d in self.images ]
        return dct

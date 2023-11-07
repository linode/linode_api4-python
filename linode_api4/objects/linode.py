import string
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from os import urandom
from random import randint
from typing import Any, Dict, List, Optional, Union
from urllib import parse

from linode_api4 import util
from linode_api4.common import load_and_validate_keys
from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects import (
    Base,
    DerivedBase,
    Image,
    JSONObject,
    Property,
    Region,
)
from linode_api4.objects.base import MappedObject
from linode_api4.objects.filtering import FilterableAttribute
from linode_api4.objects.networking import IPAddress, IPv6Range
from linode_api4.objects.vpc import VPC, VPCSubnet
from linode_api4.paginated_list import PaginatedList

PASSWORD_CHARS = string.ascii_letters + string.digits + string.punctuation


class Backup(DerivedBase):
    """
    A Backup of a Linode Instance.

    API Documentation: https://www.linode.com/docs/api/linode-instances/#backup-view
    """

    api_endpoint = "/linode/instances/{linode_id}/backups/{id}"
    derived_url_path = "backups"
    parent_id_name = "linode_id"

    properties = {
        "id": Property(identifier=True),
        "created": Property(is_datetime=True),
        "duration": Property(),
        "updated": Property(is_datetime=True),
        "finished": Property(is_datetime=True),
        "message": Property(),
        "status": Property(volatile=True),
        "type": Property(),
        "linode_id": Property(identifier=True),
        "label": Property(),
        "configs": Property(),
        "disks": Property(),
        "region": Property(slug_relationship=Region),
        "available": Property(),
    }

    def restore_to(self, linode, **kwargs):
        """
        Restores a Linode’s Backup to the specified Linode.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#backup-restore

        :param linode: The id of the Instance or the Instance to share the IPAddresses with.
                       This Instance will be able to bring up the given addresses.
        :type: linode: int or Instance

        :param kwargs: A dict containing the The ID of the Linode to restore a Backup to and
                       a boolean that, if True, deletes all Disks and Configs on
                       the target Linode before restoring.
        :type: kwargs: dict

        Example usage:
           kwargs = {
                "linode_id": 123,
                "overwrite": true
            }

        :returns: Returns true if the operation was successful
        :rtype: bool
        """

        d = {
            "linode_id": linode.id
            if issubclass(type(linode), Base)
            else linode,
        }
        d.update(kwargs)

        self._client.post(
            "{}/restore".format(Backup.api_endpoint), model=self, data=d
        )
        return True


class Disk(DerivedBase):
    """
    A Disk for the storage space on a Compute Instance.

    API Documentation: https://www.linode.com/docs/api/linode-instances/#disk-view
    """

    api_endpoint = "/linode/instances/{linode_id}/disks/{id}"
    derived_url_path = "disks"
    parent_id_name = "linode_id"

    properties = {
        "id": Property(identifier=True),
        "created": Property(is_datetime=True),
        "label": Property(mutable=True),
        "size": Property(),
        "status": Property(volatile=True),
        "filesystem": Property(),
        "updated": Property(is_datetime=True),
        "linode_id": Property(identifier=True),
    }

    def duplicate(self):
        """
        Copies a disk, byte-for-byte, into a new Disk belonging to the same Linode. The Linode must have enough
        storage space available to accept a new Disk of the same size as this one or this operation will fail.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#disk-clone

        :returns: A Disk object representing the cloned Disk
        :rtype: Disk
        """

        d = self._client.post("{}/clone".format(Disk.api_endpoint), model=self)

        if not "id" in d:
            raise UnexpectedResponseError(
                "Unexpected response duplicating disk!", json=d
            )

        return Disk(self._client, d["id"], self.linode_id)

    def reset_root_password(self, root_password=None):
        """
        Resets the password of a Disk you have permission to read_write.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#disk-root-password-reset

        :param root_password: The new root password for the OS installed on this Disk. The password must meet the complexity
                              strength validation requirements for a strong password.
        :type: root_password: str
        """
        rpass = root_password
        if not rpass:
            rpass = Instance.generate_root_password()

        params = {
            "password": rpass,
        }

        self._client.post(
            "{}/password".format(Disk.api_endpoint), model=self, data=params
        )

    def resize(self, new_size):
        """
        Resizes this disk.  The Linode Instance this disk belongs to must have
        sufficient space available to accommodate the new size, and must be
        offline.

        **NOTE** If resizing a disk down, the filesystem on the disk must still
        fit on the new disk size.  You may need to resize the filesystem on the
        disk first before performing this action.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#disk-resize

        :param new_size: The intended new size of the disk, in MB
        :type new_size: int

        :returns: True if the resize was initiated successfully.
        :rtype: bool
        """
        self._client.post(
            "{}/resize".format(Disk.api_endpoint),
            model=self,
            data={"size": new_size},
        )

        return True


class Kernel(Base):
    """
    The primary component of every Linux system. The kernel interfaces
    with the system’s hardware and it controls the operating system’s core functionality.

    Your Compute Instance is capable of running one of three kinds of kernels:

        - Upstream kernel (or distribution-supplied kernel): This kernel is maintained
          and provided by your Linux distribution. A major benefit of this kernel is that the
          distribution was designed with this kernel in mind and all updates are managed through
          the distributions package management system. It also may support features not present
          in the Linode kernel (for example, SELinux).

        - Linode kernel: Linode also maintains kernels that can be used on a Compute Instance.
          If selected, these kernels are provided to your Compute Instance at boot
          (not directly installed on your system). The Current Kernels page displays a
          list of all the available Linode kernels.

        - Custom-compiled kernel: A kernel that you compile from source. Compiling a kernel
          can let you use features not available in the upstream or Linode kernels, but it takes longer
          to compile the kernel from source than to download it from your package manager. For more
          information on custom compiled kernels, review our guides for Debian, Ubuntu, and CentOS.

    API Documentation: https://www.linode.com/docs/api/linode-instances/#kernel-view
    """

    api_endpoint = "/linode/kernels/{id}"
    properties = {
        "created": Property(is_datetime=True),
        "deprecated": Property(),
        "description": Property(),
        "id": Property(identifier=True),
        "kvm": Property(),
        "label": Property(),
        "updates": Property(),
        "version": Property(),
        "architecture": Property(),
        "xen": Property(),
        "built": Property(),
        "pvops": Property(),
    }


class Type(Base):
    """
    Linode Plan type to specify the resources available to a Linode Instance.

    API Documentation: https://www.linode.com/docs/api/linode-types/#type-view
    """

    api_endpoint = "/linode/types/{id}"
    properties = {
        "disk": Property(),
        "id": Property(identifier=True),
        "label": Property(),
        "network_out": Property(),
        "price": Property(),
        "region_prices": Property(),
        "addons": Property(),
        "memory": Property(),
        "transfer": Property(),
        "vcpus": Property(),
        "gpus": Property(),
        "successor": Property(),
        # type_class is populated from the 'class' attribute of the returned JSON
    }

    def _populate(self, json):
        """
        Allows changing the name "class" in JSON to "type_class" in python
        """
        super()._populate(json)

        if "class" in json:
            setattr(self, "type_class", json["class"])
        else:
            setattr(self, "type_class", None)

    # allow filtering on this converted type
    type_class = FilterableAttribute("class")


@dataclass
class ConfigInterfaceIPv4(JSONObject):
    vpc: str = ""
    nat_1_1: str = ""


class NetworkInterface(DerivedBase):
    """
    This class represents a Configuration Profile's network interface object.
    NOTE: This class cannot be used for the `interfaces` attribute on Config
    POST and PUT requests.

    API Documentation: TODO
    """

    api_endpoint = (
        "/linode/instances/{instance_id}/configs/{config_id}/interfaces/{id}"
    )
    derived_url_path = "interfaces"
    parent_id_name = "config_id"

    properties = {
        "id": Property(identifier=True),
        "purpose": Property(),
        "label": Property(),
        "ipam_address": Property(),
        "primary": Property(mutable=True),
        "active": Property(),
        "vpc_id": Property(id_relationship=VPC),
        "subnet_id": Property(),
        "ipv4": Property(mutable=True, json_object=ConfigInterfaceIPv4),
        "ip_ranges": Property(mutable=True),
    }

    def __init__(self, client, id, parent_id, instance_id=None, json=None):
        """
        We need a special constructor here because this object's parent
        has a parent itself.
        """
        if not instance_id and not isinstance(parent_id, tuple):
            raise ValueError(
                "ConfigInterface must either be created with a instance_id or a tuple of "
                "(config_id, instance_id) for parent_id!"
            )

        if isinstance(parent_id, tuple):
            instance_id = parent_id[1]
            parent_id = parent_id[0]

        DerivedBase.__init__(self, client, id, parent_id, json=json)

        self._set("instance_id", instance_id)

    def __repr__(self):
        return f"Interface: {self.purpose} {self.id}"

    @property
    def subnet(self) -> VPCSubnet:
        """
        Get the subnet this VPC is referencing.

        :returns: The VPCSubnet associated with this interface.
        :rtype: VPCSubnet
        """
        return VPCSubnet(self._client, self.subnet_id, self.vpc_id)


@dataclass
class ConfigInterface(JSONObject):
    """
    Represents a single interface in a Configuration Profile.
    This class only contains data about a config interface.
    If you would like to access a config interface directly,
    consider using :any:`NetworkInterface`.

    API Documentation: TODO
    """

    purpose: str = "public"

    # Public/VPC-specific
    primary: Optional[bool] = None

    # VLAN-specific
    label: Optional[str] = None
    ipam_address: Optional[str] = None

    # VPC-specific
    vpc_id: Optional[int] = None
    subnet_id: Optional[int] = None
    ipv4: Optional[Union[ConfigInterfaceIPv4, Dict[str, Any]]] = None
    ip_ranges: Optional[List[str]] = None

    # Computed
    id: int = 0

    def __repr__(self):
        return f"Interface: {self.purpose}"

    def _serialize(self):
        purpose_formats = {
            "public": {"purpose": "public", "primary": self.primary},
            "vlan": {
                "purpose": "vlan",
                "label": self.label,
                "ipam_address": self.ipam_address,
            },
            "vpc": {
                "purpose": "vpc",
                "primary": self.primary,
                "subnet_id": self.subnet_id,
                "ipv4": self.ipv4.dict
                if isinstance(self.ipv4, ConfigInterfaceIPv4)
                else self.ipv4,
                "ip_ranges": self.ip_ranges,
            },
        }

        if self.purpose not in purpose_formats:
            raise ValueError(
                f"Unknown interface purpose: {self.purpose}",
            )

        return {
            k: v
            for k, v in purpose_formats[self.purpose].items()
            if v is not None
        }


class Config(DerivedBase):
    """
    A Configuration Profile for a Linode Instance.

    API Documentation: https://www.linode.com/docs/api/linode-instances/#configuration-profile-view
    """

    api_endpoint = "/linode/instances/{linode_id}/configs/{id}"
    derived_url_path = "configs"
    parent_id_name = "linode_id"

    properties = {
        "id": Property(identifier=True),
        "linode_id": Property(identifier=True),
        "helpers": Property(mutable=True),
        "created": Property(is_datetime=True),
        "root_device": Property(mutable=True),
        "kernel": Property(relationship=Kernel, mutable=True),
        "devices": Property(),  # TODO: mutable=True),
        "initrd": Property(relationship=Disk),
        "updated": Property(),
        "comments": Property(mutable=True),
        "label": Property(mutable=True),
        "run_level": Property(mutable=True),
        "virt_mode": Property(mutable=True),
        "memory_limit": Property(mutable=True),
        "interfaces": Property(mutable=True, json_object=ConfigInterface),
    }

    @property
    def network_interfaces(self):
        """
        Returns the Network Interfaces for this Configuration Profile.
        This differs from the `interfaces` field as each NetworkInterface
        object is treated as its own API object.

        API Documentation: TODO
        """

        return [
            NetworkInterface(
                self._client, v.id, self.id, instance_id=self.linode_id
            )
            for v in self.interfaces
        ]

    def _populate(self, json):
        """
        Map devices more nicely while populating.
        """
        if json is None or len(json) < 1:
            return

        # needed here to avoid circular imports
        from .volume import Volume  # pylint: disable=import-outside-toplevel

        DerivedBase._populate(self, json)

        devices = {}
        for device_index, device in json["devices"].items():
            if not device:
                devices[device_index] = None
                continue

            dev = None
            if "disk_id" in device and device["disk_id"]:  # this is a disk
                dev = Disk.make_instance(
                    device["disk_id"], self._client, parent_id=self.linode_id
                )
            else:
                dev = Volume.make_instance(
                    device["volume_id"], self._client, parent_id=self.linode_id
                )
            devices[device_index] = dev

        self._set("devices", MappedObject(**devices))

    def _serialize(self):
        """
        Overrides _serialize to transform interfaces into json
        """
        partial = DerivedBase._serialize(self)
        interfaces = []

        for c in self.interfaces:
            if isinstance(c, ConfigInterface):
                interfaces.append(c._serialize())
            else:
                interfaces.append(c)

        partial["interfaces"] = interfaces
        return partial

    def interface_create_public(self, primary=False) -> NetworkInterface:
        """
        Creates a public interface for this Configuration Profile.

        API Documentation: TODO

        :param primary: Whether this interface is a primary interface.
        :type primary: bool

        :returns: The newly created NetworkInterface.
        :rtype: NetworkInterface

        """
        return self._interface_create({"purpose": "public", "primary": primary})

    def interface_create_vlan(
        self, label: str, ipam_address=None
    ) -> NetworkInterface:
        """
        Creates a VLAN interface for this Configuration Profile.

        API Documentation: TODO

        :param label: The label of the VLAN to associate this interface with.
        :type label: str
        :param ipam_address: The IPAM address of this interface for the associated VLAN.
        :type ipam_address: str

        :returns: The newly created NetworkInterface.
        :rtype: NetworkInterface
        """
        params = {
            "purpose": "vlan",
            "label": label,
        }
        if ipam_address is not None:
            params["ipam_address"] = ipam_address

        return self._interface_create(params)

    def interface_create_vpc(
        self,
        subnet: Union[int, VPCSubnet],
        primary=False,
        ipv4: Union[Dict[str, Any], ConfigInterfaceIPv4] = None,
        ip_ranges: Optional[List[str]] = None,
    ) -> NetworkInterface:
        """
        Creates a VPC interface for this Configuration Profile.

        API Documentation: TODO

        :param subnet: The VPC subnet to associate this interface with.
        :type subnet: int or VPCSubnet
        :param primary: Whether this is a primary interface.
        :type primary: bool
        :param ipv4: The IPv4 configuration of the interface for the associated subnet.
        :type ipv4: Dict or ConfigInterfaceIPv4
        :param ip_ranges: A list of IPs or IP ranges in the VPC subnet.
                          Packets to these CIDRs are routed through the
                          VPC network interface.
        :type ip_ranges: List of str

        :returns: The newly created NetworkInterface.
        :rtype: NetworkInterface
        """
        params = {
            "purpose": "vpc",
            "subnet_id": subnet.id if isinstance(subnet, VPCSubnet) else subnet,
            "primary": primary,
        }

        if ipv4 is not None:
            params["ipv4"] = (
                ipv4.dict if isinstance(ipv4, ConfigInterfaceIPv4) else ipv4
            )

        if ip_ranges is not None:
            params["ip_ranges"] = ip_ranges

        return self._interface_create(params)

    def interface_reorder(self, interfaces: List[Union[int, NetworkInterface]]):
        """
        Change the order of the interfaces for this Configuration Profile.

        API Documentation: TODO

        :param interfaces: A list of interfaces in the desired order.
        :type interfaces: List of str or NetworkInterface
        """
        ids = [
            v.id if isinstance(v, NetworkInterface) else v for v in interfaces
        ]

        self._client.post(
            "{}/interfaces/order".format(Config.api_endpoint),
            model=self,
            data={"ids": ids},
        )
        self.invalidate()

    def _interface_create(self, body: Dict[str, Any]) -> NetworkInterface:
        """
        The underlying ConfigInterface creation API call.
        """
        result = self._client.post(
            "{}/interfaces".format(Config.api_endpoint), model=self, data=body
        )
        self.invalidate()

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response creating Interface", json=result
            )

        i = NetworkInterface(
            self._client, result["id"], self.id, self.linode_id, result
        )
        return i


class Instance(Base):
    """
    A Linode Instance.

    API Documentation: https://www.linode.com/docs/api/linode-instances/#linode-view
    """

    api_endpoint = "/linode/instances/{id}"
    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True),
        "group": Property(mutable=True),
        "status": Property(volatile=True),
        "created": Property(is_datetime=True),
        "updated": Property(volatile=True, is_datetime=True),
        "region": Property(slug_relationship=Region),
        "alerts": Property(mutable=True),
        "image": Property(slug_relationship=Image),
        "disks": Property(derived_class=Disk),
        "configs": Property(derived_class=Config),
        "type": Property(slug_relationship=Type),
        "backups": Property(mutable=True),
        "ipv4": Property(),
        "ipv6": Property(),
        "hypervisor": Property(),
        "specs": Property(),
        "tags": Property(mutable=True),
        "host_uuid": Property(),
        "watchdog_enabled": Property(mutable=True),
        "has_user_data": Property(),
    }

    @property
    def ips(self):
        """
        The ips related collection is not normalized like the others, so we have to
        make an ad-hoc object to return for its response

        API Documentation: https://www.linode.com/docs/api/linode-instances/#networking-information-list

        :returns: A List of the ips of the Linode Instance.
        :rtype: List[IPAddress]
        """
        if not hasattr(self, "_ips"):
            result = self._client.get(
                "{}/ips".format(Instance.api_endpoint), model=self
            )

            if not "ipv4" in result:
                raise UnexpectedResponseError(
                    "Unexpected response loading IPs", json=result
                )

            v4pub = []
            for c in result["ipv4"]["public"]:
                i = IPAddress(self._client, c["address"], c)
                v4pub.append(i)

            v4pri = []
            for c in result["ipv4"]["private"]:
                i = IPAddress(self._client, c["address"], c)
                v4pri.append(i)

            shared_ips = []
            for c in result["ipv4"]["shared"]:
                i = IPAddress(self._client, c["address"], c)
                shared_ips.append(i)

            reserved = []
            for c in result["ipv4"]["reserved"]:
                i = IPAddress(self._client, c["address"], c)
                reserved.append(i)

            slaac = IPAddress(
                self._client,
                result["ipv6"]["slaac"]["address"],
                result["ipv6"]["slaac"],
            )
            link_local = IPAddress(
                self._client,
                result["ipv6"]["link_local"]["address"],
                result["ipv6"]["link_local"],
            )

            ranges = [
                IPv6Range(self._client, r["range"])
                for r in result["ipv6"]["global"]
            ]

            ips = MappedObject(
                **{
                    "ipv4": {
                        "public": v4pub,
                        "private": v4pri,
                        "shared": shared_ips,
                        "reserved": reserved,
                    },
                    "ipv6": {
                        "slaac": slaac,
                        "link_local": link_local,
                        "ranges": ranges,
                    },
                }
            )

            self._set("_ips", ips)

        return self._ips

    @property
    def available_backups(self):
        """
        The backups response contains what backups are available to be restored.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#backups-list

        :returns: A List of the available backups for the Linode Instance.
        :rtype: List[Backup]
        """
        if not hasattr(self, "_avail_backups"):
            result = self._client.get(
                "{}/backups".format(Instance.api_endpoint), model=self
            )

            if not "automatic" in result:
                raise UnexpectedResponseError(
                    "Unexpected response loading available backups!",
                    json=result,
                )

            automatic = []
            for a in result["automatic"]:
                cur = Backup(self._client, a["id"], self.id, a)
                automatic.append(cur)

            snap = None
            if result["snapshot"]["current"]:
                snap = Backup(
                    self._client,
                    result["snapshot"]["current"]["id"],
                    self.id,
                    result["snapshot"]["current"],
                )

            psnap = None
            if result["snapshot"]["in_progress"]:
                psnap = Backup(
                    self._client,
                    result["snapshot"]["in_progress"]["id"],
                    self.id,
                    result["snapshot"]["in_progress"],
                )

            self._set(
                "_avail_backups",
                MappedObject(
                    **{
                        "automatic": automatic,
                        "snapshot": {
                            "current": snap,
                            "in_progress": psnap,
                        },
                    }
                ),
            )

        return self._avail_backups

    def reset_instance_root_password(self, root_password=None):
        """
        Resets the root password for this Linode.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#linode-root-password-reset

        :param root_password: The root user’s password on this Linode. Linode passwords must
                              meet a password strength score requirement that is calculated internally
                              by the API. If the strength requirement is not met, you will receive a
                              Password does not meet strength requirement error.
        :type: root_password: str
        """
        rpass = root_password
        if not rpass:
            rpass = Instance.generate_root_password()

        params = {
            "root_pass": rpass,
        }

        self._client.post(
            "{}/password".format(Instance.api_endpoint), model=self, data=params
        )

    def transfer_year_month(self, year, month):
        """
        Get per-linode transfer for specified month

        API Documentation: https://www.linode.com/docs/api/linode-instances/#network-transfer-view-yearmonth

        :param year: Numeric value representing the year to look up.
        :type: year: int

        :param month: Numeric value representing the month to look up.
        :type: month: int

        :returns: The network transfer statistics for the specified month.
        :rtype: MappedObject
        """

        result = self._client.get(
            "{}/transfer/{}/{}".format(
                Instance.api_endpoint,
                parse.quote(str(year)),
                parse.quote(str(month)),
            ),
            model=self,
        )

        return MappedObject(**result)

    @property
    def transfer(self):
        """
        Get per-linode transfer

        API Documentation: https://www.linode.com/docs/api/linode-instances/#network-transfer-view

        :returns: The network transfer statistics for the current month.
        :rtype: MappedObject
        """
        if not hasattr(self, "_transfer"):
            result = self._client.get(
                "{}/transfer".format(Instance.api_endpoint), model=self
            )

            if not "used" in result:
                raise UnexpectedResponseError(
                    "Unexpected response when getting Transfer Pool!"
                )

            mapped = MappedObject(**result)

            setattr(self, "_transfer", mapped)

        return self._transfer

    def _populate(self, json):
        if json is not None:
            # fixes ipv4 and ipv6 attribute of json to make base._populate work
            if "ipv4" in json and "address" in json["ipv4"]:
                json["ipv4"]["id"] = json["ipv4"]["address"]
            if "ipv6" in json and isinstance(json["ipv6"], list):
                for j in json["ipv6"]:
                    j["id"] = j["range"]

        Base._populate(self, json)

    def invalidate(self):
        """Clear out cached properties"""
        if hasattr(self, "_avail_backups"):
            del self._avail_backups
        if hasattr(self, "_ips"):
            del self._ips
        if hasattr(self, "_transfer"):
            del self._transfer

        Base.invalidate(self)

    def boot(self, config=None):
        """
        Boots a Linode you have permission to modify. If no parameters are given, a Config
        profile will be chosen for this boot based on the following criteria:

            - If there is only one Config profile for this Linode, it will be used.
            - If there is more than one Config profile, the last booted config will be used.
            - If there is more than one Config profile and none were the last to be booted
              (because the Linode was never booted or the last booted config was deleted)
              an error will be returned.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#linode-boot

        :param config: The Linode Config ID to boot into.
        :type: config: int

        :returns: True if the operation was successful.
        :rtype: bool
        """

        resp = self._client.post(
            "{}/boot".format(Instance.api_endpoint),
            model=self,
            data={"config_id": config.id} if config else None,
        )

        if "error" in resp:
            return False
        return True

    def shutdown(self):
        """
        Shuts down a Linode you have permission to modify. If any actions
        are currently running or queued, those actions must be completed
        first before you can initiate a shutdown.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#linode-shut-down

        :returns: True if the operation was successful.
        :rtype: bool
        """

        resp = self._client.post(
            "{}/shutdown".format(Instance.api_endpoint), model=self
        )

        if "error" in resp:
            return False
        return True

    def reboot(self):
        """
        Reboots a Linode you have permission to modify. If any actions are currently running
        or queued, those actions must be completed first before you can initiate a reboot.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#linode-reboot

        :returns: True if the operation was successful.
        :rtype: bool
        """

        resp = self._client.post(
            "{}/reboot".format(Instance.api_endpoint), model=self
        )

        if "error" in resp:
            return False
        return True

    def resize(self, new_type, allow_auto_disk_resize=True, **kwargs):
        """
        Resizes a Linode you have the read_write permission to a different Type. If any
        actions are currently running or queued, those actions must be completed first
        before you can initiate a resize. Additionally, the following criteria must be
        met in order to resize a Linode:

            - The Linode must not have a pending migration.
            - Your Account cannot have an outstanding balance.
            - The Linode must not have more disk allocation than the new Type allows.
                - In that situation, you must first delete or resize the disk to be smaller.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#linode-resize

        :param new_type: The Linode Type or the id representing it.
        :type: new_type: Type or int

        :param allow_auto_disk_resize: Automatically resize disks when resizing a Linode.
                                       When resizing down to a smaller plan your Linode’s
                                       data must fit within the smaller disk size. Defaults to true.
        :type: allow_auto_disk_resize: bool

        :returns: True if the operation was successful.
        :rtype: bool
        """

        new_type = new_type.id if issubclass(type(new_type), Base) else new_type

        params = {
            "type": new_type,
            "allow_auto_disk_resize": allow_auto_disk_resize,
        }
        params.update(kwargs)

        resp = self._client.post(
            "{}/resize".format(Instance.api_endpoint), model=self, data=params
        )

        if "error" in resp:
            return False
        return True

    @staticmethod
    def generate_root_password():
        def _func(value):
            if sys.version_info[0] < 3:
                value = int(value.encode("hex"), 16)
            return value

        password = "".join(
            [
                PASSWORD_CHARS[_func(c) % len(PASSWORD_CHARS)]
                for c in urandom(randint(50, 110))
            ]
        )

        # ensure the generated password is not too long
        if len(password) > 110:
            password = password[:110]

        return password

    # create derived objects
    def config_create(
        self,
        kernel=None,
        label=None,
        devices=[],
        disks=[],
        volumes=[],
        interfaces=[],
        **kwargs,
    ):
        """
        Creates a Linode Config with the given attributes.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#configuration-profile-create

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
        # needed here to avoid circular imports
        from .volume import Volume  # pylint: disable=import-outside-toplevel

        hypervisor_prefix = "sd" if self.hypervisor == "kvm" else "xvd"
        device_names = [
            hypervisor_prefix + string.ascii_lowercase[i] for i in range(0, 8)
        ]
        device_map = {
            device_names[i]: None for i in range(0, len(device_names))
        }

        if devices and (disks or volumes):
            raise ValueError(
                'You may not call config_create with "devices" and '
                'either of "disks" or "volumes" specified!'
            )

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
            raise ValueError("Must include at least one disk or volume!")

        for i, d in enumerate(devices):
            if d is None:
                pass
            elif isinstance(d, Disk):
                device_map[device_names[i]] = {"disk_id": d.id}
            elif isinstance(d, Volume):
                device_map[device_names[i]] = {"volume_id": d.id}
            else:
                raise TypeError("Disk or Volume expected!")

        param_interfaces = []
        for interface in interfaces:
            if isinstance(interface, ConfigInterface):
                interface = interface._serialize()
            param_interfaces.append(interface)

        params = {
            "kernel": kernel.id if issubclass(type(kernel), Base) else kernel,
            "label": label
            if label
            else "{}_config_{}".format(self.label, len(self.configs)),
            "devices": device_map,
            "interfaces": param_interfaces,
        }
        params.update(kwargs)

        result = self._client.post(
            "{}/configs".format(Instance.api_endpoint), model=self, data=params
        )
        self.invalidate()

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response creating config!", json=result
            )

        c = Config(self._client, result["id"], self.id, result)
        return c

    def disk_create(
        self,
        size,
        label=None,
        filesystem=None,
        read_only=False,
        image=None,
        root_pass=None,
        authorized_keys=None,
        authorized_users=None,
        stackscript=None,
        **stackscript_args,
    ):
        """
        Creates a new Disk for this Instance.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#disk-create

        :param size: The size of the disk, in MB
        :param label: The label of the disk.  If not given, a default label will be generated.
        :param filesystem: The filesystem type for the disk.  If not given, the default
                           for the image deployed the disk will be used.  Required
                           if creating a disk without an image.
        :param read_only: If True, creates a read-only disk
        :param image: The Image to deploy to the disk.
        :param root_pass: The password to configure for the root user when deploying an
                          image to this disk.  Not used if image is not given.  If an
                          image is given and root_pass is not, a password will be
                          generated and returned alongside the new disk.
        :param authorized_keys: A list of SSH keys to install as trusted for the root user.
        :param authorized_users: A list of usernames whose keys should be installed
                                 as trusted for the root user.  These user's keys
                                 should already be set up, see :any:`ProfileGroup.ssh_keys`
                                 for details.
        :param stackscript: A StackScript object, or the ID of one, to deploy to this
                            disk.  Requires deploying a compatible image.
        :param **stackscript_args: Any arguments to pass to the StackScript, as defined
                                   by its User Defined Fields.
        """

        gen_pass = None
        if image and not root_pass:
            gen_pass = Instance.generate_root_password()
            root_pass = gen_pass

        authorized_keys = load_and_validate_keys(authorized_keys)

        if image and not label:
            label = "My {} Disk".format(image.label)

        params = {
            "size": size,
            "label": label
            if label
            else "{}_disk_{}".format(self.label, len(self.disks)),
            "read_only": read_only,
            "filesystem": filesystem,
            "authorized_keys": authorized_keys,
            "authorized_users": authorized_users,
        }

        if image:
            params.update(
                {
                    "image": image.id
                    if issubclass(type(image), Base)
                    else image,
                    "root_pass": root_pass,
                }
            )

        if stackscript:
            params["stackscript_id"] = stackscript.id
            if stackscript_args:
                params["stackscript_data"] = stackscript_args

        result = self._client.post(
            "{}/disks".format(Instance.api_endpoint), model=self, data=params
        )
        self.invalidate()

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response creating disk!", json=result
            )

        d = Disk(self._client, result["id"], self.id, result)

        if gen_pass:
            return d, gen_pass
        return d

    def enable_backups(self):
        """
        Enable Backups for this Instance.  When enabled, we will automatically
        backup your Instance's data so that it can be restored at a later date.
        For more information on Instance's Backups service and pricing, see our
        Backups Page: https://www.linode.com/backups

        API Documentation: https://www.linode.com/docs/api/linode-instances/#backups-enable

        :returns: True if the operation was successful.
        :rtype: bool
        """
        self._client.post(
            "{}/backups/enable".format(Instance.api_endpoint), model=self
        )
        self.invalidate()
        return True

    def cancel_backups(self):
        """
        Cancels Backups for this Instance.  All existing Backups will be lost,
        including any snapshots that have been taken.  This cannot be undone,
        but Backups can be re-enabled at a later date.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#backups-cancel

        :returns: True if the operation was successful.
        :rtype: bool
        """
        self._client.post(
            "{}/backups/cancel".format(Instance.api_endpoint), model=self
        )
        self.invalidate()
        return True

    def snapshot(self, label=None):
        """
        Creates a snapshot Backup of a Linode.

        Important: If you already have a snapshot of this Linode, this
        is a destructive action. The previous snapshot will be deleted.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#snapshot-create

        :param label: The label for the new snapshot.
        :type: label: str

        :returns: The snapshot Backup created.
        :rtype: Backup
        """

        result = self._client.post(
            "{}/backups".format(Instance.api_endpoint),
            model=self,
            data={"label": label},
        )

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response taking snapshot!", json=result
            )

        # so the changes show up the next time they're accessed
        if hasattr(self, "_avail_backups"):
            del self._avail_backups

        b = Backup(self._client, result["id"], self.id, result)
        return b

    def ip_allocate(self, public=False):
        """
        Allocates a new :any:`IPAddress` for this Instance.  Additional public
        IPs require justification, and you may need to open a :any:`SupportTicket`
        before you can add one.  You may only have, at most, one private IP per
        Instance.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#ipv4-address-allocate

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
            },
        )

        if not "address" in result:
            raise UnexpectedResponseError(
                "Unexpected response allocating IP!", json=result
            )

        i = IPAddress(self._client, result["address"], result)
        return i

    def rebuild(self, image, root_pass=None, authorized_keys=None, **kwargs):
        """
        Rebuilding an Instance deletes all existing Disks and Configs and deploys
        a new :any:`Image` to it.  This can be used to reset an existing
        Instance or to install an Image on an empty Instance.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#linode-rebuild

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
            "image": image.id if issubclass(type(image), Base) else image,
            "root_pass": root_pass,
            "authorized_keys": authorized_keys,
        }
        params.update(kwargs)

        result = self._client.post(
            "{}/rebuild".format(Instance.api_endpoint), model=self, data=params
        )

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response issuing rebuild!", json=result
            )

        # update ourself with the newly-returned information
        self._populate(result)

        if not ret_pass:
            return True
        else:
            return ret_pass

    def rescue(self, *disks):
        """
        Rescue Mode is a safe environment for performing many system recovery and disk management
        tasks. Rescue Mode is based on the Finnix recovery distribution, a self-contained and bootable
        Linux distribution. You can also use Rescue Mode for tasks other than disaster recovery,
        such as formatting disks to use different filesystems, copying data between disks, and
        downloading files from a disk via SSH and SFTP.

        Note that “sdh” is reserved and unavailable during rescue.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#linode-boot-into-rescue-mode

        :param disks: Devices that are either Disks or Volumes
        :type: disks: dict

        Example usage:
            disks = {
                "sda": {
                    "disk_id": 124458,
                    "volume_id": null
                },
                "sdb": {
                    "disk_id": null,
                    "volume_id": null
                }
            }
        """

        if disks:
            disks = {
                x: {"disk_id": y}
                for x, y in zip(
                    ("sda", "sdb", "sdc", "sdd", "sde", "sdf", "sdg"), disks
                )
            }
        else:
            disks = None

        result = self._client.post(
            "{}/rescue".format(Instance.api_endpoint),
            model=self,
            data={"devices": disks},
        )

        return result

    def mutate(self, allow_auto_disk_resize=True):
        """
        Upgrades this Instance to the latest generation type

        API Documentation: https://www.linode.com/docs/api/linode-instances/#linode-upgrade

        :param allow_auto_disk_resize: Automatically resize disks when resizing a Linode.
                                       When resizing down to a smaller plan your Linode’s
                                       data must fit within the smaller disk size. Defaults to true.
        :type: allow_auto_disk_resize: bool

        :returns: True if the operation was successful.
        :rtype: bool
        """

        params = {"allow_auto_disk_resize": allow_auto_disk_resize}

        self._client.post(
            "{}/mutate".format(Instance.api_endpoint), model=self, data=params
        )

        return True

    def initiate_migration(self, region=None, upgrade=None):
        """
        Initiates a pending migration that is already scheduled for this Linode
        Instance

        API Documentation: https://www.linode.com/docs/api/linode-instances/#dc-migrationpending-host-migration-initiate

        :param region: The region to which the Linode will be migrated. Must be a valid region slug.
                       A list of regions can be viewed by using the GET /regions endpoint. A cross data
                       center migration will cancel a pending migration that has not yet been initiated.
                       A cross data center migration will initiate a linode_migrate_datacenter_create event.
        :type: region: str

        :param upgrade: When initiating a cross DC migration, setting this value to true will also ensure
                        that the Linode is upgraded to the latest generation of hardware that corresponds to
                        your Linode’s Type, if any free upgrades are available for it. If no free upgrades
                        are available, and this value is set to true, then the endpoint will return a 400
                        error code and the migration will not be performed. If the data center set in the
                        region field does not allow upgrades, then the endpoint will return a 400 error
                        code and the migration will not be performed.
        :type: upgrade: bool
        """
        params = {
            "region": region.id if issubclass(type(region), Base) else region,
            "upgrade": upgrade,
        }

        util.drop_null_keys(params)

        self._client.post(
            "{}/migrate".format(Instance.api_endpoint), model=self, data=params
        )

    def firewalls(self):
        """
        View Firewall information for Firewalls associated with this Linode.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#firewalls-list

        :returns: A List of Firewalls of the Linode Instance.
        :rtype: List[Firewall]
        """
        from linode_api4.objects import (  # pylint: disable=import-outside-toplevel
            Firewall,
        )

        result = self._client.get(
            "{}/firewalls".format(Instance.api_endpoint), model=self
        )

        return [
            Firewall(self._client, firewall["id"])
            for firewall in result["data"]
        ]

    def nodebalancers(self):
        """
        View a list of NodeBalancers that are assigned to this Linode and readable by the requesting User.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#linode-nodebalancers-view

        :returns: A List of Nodebalancers of the Linode Instance.
        :rtype: List[Nodebalancer]
        """
        from linode_api4.objects import (  # pylint: disable=import-outside-toplevel
            NodeBalancer,
        )

        result = self._client.get(
            "{}/nodebalancers".format(Instance.api_endpoint), model=self
        )

        return [
            NodeBalancer(self._client, nodebalancer["id"])
            for nodebalancer in result["data"]
        ]

    def volumes(self):
        """
        View Block Storage Volumes attached to this Linode.

        API Documentation: https://www.linode.com/docs/api/linode-instances/#linodes-volumes-list

        :returns: A List of Volumes of the Linode Instance.
        :rtype: List[Volume]
        """
        from linode_api4.objects import (  # pylint: disable=import-outside-toplevel
            Volume,
        )

        result = self._client.get(
            "{}/volumes".format(Instance.api_endpoint), model=self
        )

        return [Volume(self._client, volume["id"]) for volume in result["data"]]

    def clone(
        self,
        to_linode=None,
        region=None,
        instance_type=None,
        configs=[],
        disks=[],
        label=None,
        group=None,
        with_backups=None,
    ):
        """
        Clones this linode into a new linode or into a new linode in the given region

        API Documentation: https://www.linode.com/docs/api/linode-instances/#linode-clone

        :param to_linode: If an existing Linode is the target for the clone, the ID of that
                          Linode. The existing Linode must have enough resources to accept the clone.
        :type: to_linode: int

        :param region: This is the Region where the Linode will be deployed. Region can only be
                       provided and is required when cloning to a new Linode.
        :type: region: str

        :param instance_type: A Linode’s Type determines what resources are available to it, including disk space,
                              memory, and virtual cpus. The amounts available to a specific Linode are
                              returned as specs on the Linode object.
        :type: instance_type: str

        :param configs: An array of configuration profile IDs.
        :type: configs: List of int

        :param disks: An array of disk IDs.
        :type: disks: List of int

        :param label: The label to assign this Linode when cloning to a new Linode.
        :type: label: str

        :param group: A label used to group Linodes for display. Linodes are not required to have a group.
        :type: group: str

        :param with_backups: If this field is set to true, the created Linode will automatically be
                             enrolled in the Linode Backup service. This will incur an additional charge.
        :type: with_backups: bool

        :returns: The cloned Instance.
        :rtype: Instance
        """
        if to_linode and region:
            raise ValueError(
                'You may only specify one of "to_linode" and "region"'
            )

        if region and not type:
            raise ValueError('Specifying a region requires a "service" as well')

        if not isinstance(configs, list) and not isinstance(
            configs, PaginatedList
        ):
            configs = [configs]
        if not isinstance(disks, list) and not isinstance(disks, PaginatedList):
            disks = [disks]

        cids = [c.id if issubclass(type(c), Base) else c for c in configs]
        dids = [d.id if issubclass(type(d), Base) else d for d in disks]

        params = {
            "linode_id": to_linode.id
            if issubclass(type(to_linode), Base)
            else to_linode,
            "region": region.id if issubclass(type(region), Base) else region,
            "type": instance_type.id
            if issubclass(type(instance_type), Base)
            else instance_type,
            "configs": cids if cids else None,
            "disks": dids if dids else None,
            "label": label,
            "group": group,
            "with_backups": with_backups,
        }

        result = self._client.post(
            "{}/clone".format(Instance.api_endpoint), model=self, data=params
        )

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response cloning Instance!", json=result
            )

        l = Instance(self._client, result["id"], result)
        return l

    @property
    def stats(self):
        """
        Returns the JSON stats for this Instance

        API Documentation: https://www.linode.com/docs/api/linode-instances/#linode-statistics-view

        :returns: The JSON stats for this Instance
        :rtype: dict
        """
        # TODO - this would be nicer if we formatted the stats
        return self._client.get(
            "{}/stats".format(Instance.api_endpoint), model=self
        )

    def stats_for(self, dt):
        """
        Returns stats for the month containing the given datetime

        API Documentation: https://www.linode.com/docs/api/linode-instances/#statistics-view-yearmonth

        :param dt: A Datetime for which to return statistics
        :type: dt: Datetime

        :returns: The JSON stats for this Instance at the specified Datetime
        :rtype: dict
        """
        # TODO - this would be nicer if we formatted the stats
        if not isinstance(dt, datetime):
            raise TypeError("stats_for requires a datetime object!")
        return self._client.get(
            "{}/stats/{}".format(
                Instance.api_endpoint, parse.quote(dt.strftime("%Y/%m"))
            ),
            model=self,
        )


class UserDefinedFieldType(Enum):
    text = 1
    select_one = 2
    select_many = 3


class UserDefinedField:
    def __init__(self, name, label, example, field_type, choices=None):
        self.name = name
        self.label = label
        self.example = example
        self.field_type = field_type
        self.choices = choices

    def __repr__(self):
        return "{}({}): {}".format(
            self.label, self.field_type.name, self.example
        )


class StackScript(Base):
    """
    A script allowing users to reproduce specific software configurations
    when deploying Compute Instances, with more user control than static system images.

    API Documentation: https://www.linode.com/docs/api/stackscripts/#stackscript-view
    """

    api_endpoint = "/linode/stackscripts/{id}"
    properties = {
        "user_defined_fields": Property(),
        "label": Property(mutable=True),
        "rev_note": Property(mutable=True),
        "username": Property(),
        "user_gravatar_id": Property(),
        "is_public": Property(mutable=True),
        "created": Property(is_datetime=True),
        "deployments_active": Property(),
        "script": Property(mutable=True),
        "images": Property(mutable=True),  # TODO make slug_relationship
        "deployments_total": Property(),
        "description": Property(mutable=True),
        "updated": Property(is_datetime=True),
        "mine": Property(),
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
            if hasattr(udf, "oneof"):
                t = UserDefinedFieldType.select_one
                choices = udf.oneof.split(",")
            elif hasattr(udf, "manyof"):
                t = UserDefinedFieldType.select_many
                choices = udf.manyof.split(",")

            mapped_udfs.append(
                UserDefinedField(
                    udf.name,
                    udf.label if hasattr(udf, "label") else None,
                    udf.example if hasattr(udf, "example") else None,
                    t,
                    choices=choices,
                )
            )

        self._set("user_defined_fields", mapped_udfs)
        ndist = [Image(self._client, d) for d in self.images]
        self._set("images", ndist)

    def _serialize(self):
        dct = Base._serialize(self)
        dct["images"] = [d.id for d in self.images]
        return dct

import base64
import os
from collections.abc import Iterable
from typing import Any, Dict, Optional, Union

from linode_api4.common import load_and_validate_keys
from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import (
    ConfigInterface,
    Firewall,
    Instance,
    InstanceDiskEncryptionType,
    Kernel,
    PlacementGroup,
    StackScript,
    Type,
)
from linode_api4.objects.base import _flatten_request_body_recursive
from linode_api4.objects.filtering import Filter
from linode_api4.objects.linode import (
    Backup,
    InstancePlacementGroupAssignment,
    _expand_placement_group_assignment,
)
from linode_api4.util import drop_null_keys


class LinodeGroup(Group):
    """
    Encapsulates Linode-related methods of the :any:`LinodeClient`.  This
    should not be instantiated on its own, but should instead be used through
    an instance of :any:`LinodeClient`::

       client = LinodeClient(token)
       instances = client.linode.instances() # use the LinodeGroup

    This group contains all features beneath the `/linode` group in the API v4.
    """

    def types(self, *filters):
        """
        Returns a list of Linode Instance types.  These may be used to create
        or resize Linodes, or simply referenced on their own.  Types can be
        filtered to return specific types, for example::

           standard_types = client.linode.types(Type.class == "standard")

        API documentation: https://techdocs.akamai.com/linode-api/reference/get-linode-types

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of types that match the query.
        :rtype: PaginatedList of Type
        """
        return self.client._get_and_filter(Type, *filters)

    def instances(self, *filters):
        """
        Returns a list of Linode Instances on your account.  You may filter
        this query to return only Linodes that match specific criteria::

           prod_linodes = client.linode.instances(Instance.group == "prod")

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-linode-instances

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Instances that matched the query.
        :rtype: PaginatedList of Instance
        """
        return self.client._get_and_filter(Instance, *filters)

    def stackscripts(self, *filters, **kwargs):
        """
        Returns a list of :any:`StackScripts<StackScript>`, both public and
        private.  You may filter this query to return only
        :any:`StackScripts<StackScript>` that match certain criteria.  You may
        also request only your own private :any:`StackScripts<StackScript>`::

           my_stackscripts = client.linode.stackscripts(mine_only=True)

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-stack-scripts

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.
        :param mine_only: If True, returns only private StackScripts
        :type mine_only: bool

        :returns: A list of StackScripts matching the query.
        :rtype: PaginatedList of StackScript
        """
        # python2 can't handle *args and a single keyword argument, so this is a workaround
        if "mine_only" in kwargs:
            if kwargs["mine_only"]:
                new_filter = Filter({"mine": True})
                if filters:
                    filters = list(filters)
                    filters[0] = filters[0] & new_filter
                else:
                    filters = [new_filter]

            del kwargs["mine_only"]

        if kwargs:
            raise TypeError(
                "stackscripts() got unexpected keyword argument '{}'".format(
                    kwargs.popitem()[0]
                )
            )

        return self.client._get_and_filter(StackScript, *filters)

    def kernels(self, *filters):
        """
        Returns a list of available :any:`Kernels<Kernel>`.  Kernels are used
        when creating or updating :any:`LinodeConfigs,LinodeConfig>`.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-kernels

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of available kernels that match the query.
        :rtype: PaginatedList of Kernel
        """
        return self.client._get_and_filter(Kernel, *filters)

    # create things
    def instance_create(
        self,
        ltype,
        region,
        image=None,
        authorized_keys=None,
        firewall: Optional[Union[Firewall, int]] = None,
        backup: Optional[Union[Backup, int]] = None,
        stackscript: Optional[Union[StackScript, int]] = None,
        disk_encryption: Optional[
            Union[InstanceDiskEncryptionType, str]
        ] = None,
        placement_group: Optional[
            Union[
                InstancePlacementGroupAssignment,
                PlacementGroup,
                Dict[str, Any],
                int,
            ]
        ] = None,
        **kwargs,
    ):
        """
        Creates a new Linode Instance. This function has several modes of operation:

        **Create an Instance from an Image**

        To create an Instance from an :any:`Image`, call `instance_create` with
        a :any:`Type`, a :any:`Region`, and an :any:`Image`.  All three of
        these fields may be provided as either the ID or the appropriate object.
        In this mode, a root password will be generated and returned with the
        new Instance object.

        For example::

           new_linode, password = client.linode.instance_create(
               "g6-standard-2",
               "us-east",
               image="linode/debian9")

           ltype = client.linode.types().first()
           region = client.regions().first()
           image = client.images().first()

           another_linode, password = client.linode.instance_create(
               ltype,
               region,
               image=image)

        To output the password from the above example:
            print(password)

        To output the first IPv4 address of the new Linode:
            print(new_linode.ipv4[0])

        To delete the new_linode (WARNING: this immediately destroys the Linode):
            new_linode.delete()

        **Create an Instance from StackScript**

        When creating an Instance from a :any:`StackScript`, an :any:`Image` that
        the StackScript support must be provided..  You must also provide any
        required StackScript data for the script's User Defined Fields..  For
        example, if deploying `StackScript 10079`_ (which deploys a new Instance
        with a user created from keys on `github`_::

           stackscript = StackScript(client, 10079)

           new_linode, password = client.linode.instance_create(
              "g6-standard-2",
              "us-east",
              image="linode/debian9",
              stackscript=stackscript,
              stackscript_data={"gh_username": "example"})

        In the above example, "gh_username" is the name of a User Defined Field
        in the chosen StackScript.  For more information on StackScripts, see
        the `StackScript guide`_.

        .. _`StackScript 10079`: https://www.linode.com/stackscripts/view/10079
        .. _`github`: https://github.com
        .. _`StackScript guide`: https://www.linode.com/docs/platform/stackscripts/

        **Create an Instance from a Backup**

        To create a new Instance by restoring a :any:`Backup` to it, provide a
        :any:`Type`, a :any:`Region`, and the :any:`Backup` to restore.  You
        may provide either IDs or objects for all of these fields::

           existing_linode = Instance(client, 123)
           snapshot = existing_linode.available_backups.snapshot.current

           new_linode = client.linode.instance_create(
               "g6-standard-2",
               "us-east",
               backup=snapshot)

        **Create an empty Instance**

        If you want to create an empty Instance that you will configure manually,
        simply call `instance_create` with a :any:`Type` and a :any:`Region`::

           empty_linode = client.linode.instance_create("g6-standard-2", "us-east")

        When created this way, the Instance will not be booted and cannot boot
        successfully until disks and configs are created, or it is otherwise
        configured.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-linode-instance

        :param ltype: The Instance Type we are creating
        :type ltype: str or Type
        :param region: The Region in which we are creating the Instance
        :type region: str or Region
        :param image: The Image to deploy to this Instance. If this is provided
                      and no root_pass is given, a password will be generated
                      and returned along with the new Instance.
        :type image: str or Image
        :param stackscript: The StackScript to deploy to the new Instance.  If
                            provided, "image" is required and must be compatible
                            with the chosen StackScript.
        :type stackscript: int or StackScript
        :param stackscript_data: Values for the User Defined Fields defined in
                                 the chosen StackScript.  Does nothing if
                                 StackScript is not provided.
        :type stackscript_data: dict
        :param backup: The Backup to restore to the new Instance.  May not be
                       provided if "image" is given.
        :type backup: int of Backup
        :param authorized_keys: The ssh public keys to install in the linode's
                                /root/.ssh/authorized_keys file.  Each entry may
                                be a single key, or a path to a file containing
                                the key.
        :type authorized_keys: list or str
        :param label: The display label for the new Instance
        :type label: str
        :param group: The display group for the new Instance
        :type group: str
        :param booted: Whether the new Instance should be booted.  This will
                       default to True if the Instance is deployed from an Image
                       or Backup.
        :type booted: bool
        :param tags: A list of tags to apply to the new instance.  If any of the
                     tags included do not exist, they will be created as part of
                     this operation.
        :type tags: list[str]
        :param private_ip: Whether the new Instance should have private networking
                           enabled and assigned a private IPv4 address.
        :type private_ip: bool
        :param metadata: Metadata-related fields to use when creating the new Instance.
                         The contents of this field can be built using the
                         :any:`build_instance_metadata` method.
        :type metadata: dict
        :param firewall: The firewall to attach this Linode to.
        :type firewall: int or Firewall
        :param disk_encryption: The disk encryption policy for this Linode.
                                NOTE: Disk encryption may not currently be available to all users.
        :type disk_encryption: InstanceDiskEncryptionType or str
        :param interfaces: An array of Network Interfaces to add to this Linode’s Configuration Profile.
                           At least one and up to three Interface objects can exist in this array.
        :type interfaces: list[ConfigInterface] or list[dict[str, Any]]
        :param placement_group: A Placement Group to create this Linode under.
        :type placement_group: Union[InstancePlacementGroupAssignment, PlacementGroup, Dict[str, Any], int]

        :returns: A new Instance object, or a tuple containing the new Instance and
                  the generated password.
        :rtype: Instance or tuple(Instance, str)
        :raises ApiError: If contacting the API fails
        :raises UnexpectedResponseError: If the API response is somehow malformed.
                                         This usually indicates that you are using
                                         an outdated library.
        """

        ret_pass = None
        if image and not "root_pass" in kwargs:
            ret_pass = Instance.generate_root_password()
            kwargs["root_pass"] = ret_pass

        interfaces = kwargs.get("interfaces", None)
        if interfaces is not None and isinstance(interfaces, Iterable):
            kwargs["interfaces"] = [
                i._serialize() if isinstance(i, ConfigInterface) else i
                for i in interfaces
            ]

        params = {
            "type": ltype,
            "region": region,
            "image": image,
            "authorized_keys": load_and_validate_keys(authorized_keys),
            # These will automatically be flattened below
            "firewall_id": firewall,
            "backup_id": backup,
            "stackscript_id": stackscript,
            # Special cases
            "disk_encryption": (
                str(disk_encryption) if disk_encryption else None
            ),
            "placement_group": (
                _expand_placement_group_assignment(placement_group)
                if placement_group
                else None
            ),
        }

        params.update(kwargs)

        result = self.client.post(
            "/linode/instances",
            data=_flatten_request_body_recursive(drop_null_keys(params)),
        )

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating linode!", json=result
            )

        l = Instance(self.client, result["id"], result)
        if not ret_pass:
            return l
        return l, ret_pass

    @staticmethod
    def build_instance_metadata(user_data=None, encode_user_data=True):
        """
        Builds the contents of the ``metadata`` field to be passed into
        the :any:`instance_create` method. This helper can also be used
        when cloning and rebuilding Instances.
        **Creating an Instance with User Data**::
            new_linode, password = client.linode.instance_create(
                "g6-standard-2",
                "us-east",
                image="linode/ubuntu22.04",
                metadata=client.linode.build_instance_metadata(user_data="myuserdata")
            )
        :param user_data: User-defined data to provide to the Linode Instance through
                          the Metadata service.
        :type user_data: str
        :param encode_user_data: If true, the provided user_data field will be automatically
                                 encoded to a valid base64 string. This field should only
                                 be set to false if the user_data param is already base64-encoded.
        :type encode_user_data: bool
        :returns: The built ``metadata`` structure.
        :rtype: dict
        """
        result = {}

        if user_data is not None:
            result["user_data"] = (
                base64.b64encode(user_data.encode()).decode()
                if encode_user_data
                else user_data
            )

        return result

    def stackscript_create(
        self, label, script, images, desc=None, public=False, **kwargs
    ):
        """
        Creates a new :any:`StackScript` on your account.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-add-stack-script

        :param label: The label for this StackScript.
        :type label: str
        :param script: The script to run when an :any:`Instance` is deployed with
                       this StackScript.  Must begin with a shebang (#!).
        :type script: str
        :param images: A list of :any:`Images<Image>` that this StackScript
                       supports.  Instances will not be deployed from this
                       StackScript unless deployed from one of these Images.
        :type images: list of Image
        :param desc: A description for this StackScript.
        :type desc: str
        :param public: Whether this StackScript is public.  Defaults to False.
                       Once a StackScript is made public, it may not be set
                       back to private.
        :type public: bool

        :returns: The new StackScript
        :rtype: StackScript
        """

        script_body = script
        if not script.startswith("#!"):
            # it doesn't look like a stackscript body, let's see if it's a file
            if os.path.isfile(script):
                with open(script) as f:
                    script_body = f.read()
            else:
                raise ValueError(
                    "script must be the script text or a path to a file"
                )

        params = {
            "label": label,
            "images": images,
            "is_public": public,
            "script": script_body,
            "description": desc if desc else "",
        }
        params.update(kwargs)

        result = self.client.post(
            "/linode/stackscripts",
            data=_flatten_request_body_recursive(params),
        )

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating StackScript!", json=result
            )

        s = StackScript(self.client, result["id"], result)
        return s

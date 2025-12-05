from linode_api4.common import Price, RegionPrice
from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects.base import (
    Base,
    Property,
    _flatten_request_body_recursive,
)
from linode_api4.objects.linode import Instance, Region
from linode_api4.objects.region import Region
from linode_api4.util import drop_null_keys


class VolumeType(Base):
    """
    An VolumeType represents the structure of a valid Volume type.
    Currently the VolumeType can only be retrieved by listing, i.e.:
        types = client.volumes.types()

    API documentation: https://techdocs.akamai.com/linode-api/reference/get-volume-types
    """

    properties = {
        "id": Property(identifier=True),
        "label": Property(),
        "price": Property(json_object=Price),
        "region_prices": Property(json_object=RegionPrice),
        "transfer": Property(),
    }


class Volume(Base):
    """
    A single Block Storage Volume. Block Storage Volumes are persistent storage devices
    that can be attached to a Compute Instance and used to store any type of data.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-volume
    """

    api_endpoint = "/volumes/{id}"

    properties = {
        "id": Property(identifier=True),
        "created": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
        "linode_id": Property(id_relationship=Instance),
        "label": Property(mutable=True),
        "size": Property(),
        "status": Property(),
        "region": Property(slug_relationship=Region),
        "tags": Property(mutable=True, unordered=True),
        "filesystem_path": Property(),
        "hardware_type": Property(),
        "linode_label": Property(),
        "encryption": Property(),
    }

    def attach(self, to_linode, config=None):
        """
        Attaches this Volume to the given Linode.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-attach-volume

        :param to_linode: The ID or object of the Linode to attach the volume to.
        :type to_linode: Union[Instance, int]

        :param config: The ID or object of the Linode Config to include this Volume in.
                       Must belong to the Linode referenced by linode_id.
                       If not given, the last booted Config will be chosen.
        :type config: Union[Config, int]
        """

        body = {
            "linode_id": to_linode,
            "config": config,
        }

        result = self._client.post(
            "{}/attach".format(Volume.api_endpoint),
            model=self,
            data=_flatten_request_body_recursive(drop_null_keys(body)),
        )

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when attaching volume!", json=result
            )

        self._populate(result)
        return True

    def detach(self):
        """
        Detaches this Volume if it is attached

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-detach-volume

        :returns: Returns true if operation was successful
        :rtype: bool
        """
        self._client.post("{}/detach".format(Volume.api_endpoint), model=self)

        return True

    def resize(self, size):
        """
        Resizes this Volume

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-resize-volume

        :param size: The Volume’s size, in GiB.
        :type size: int

        :returns: Returns true if operation was successful
        :rtype: bool
        """
        result = self._client.post(
            "{}/resize".format(Volume.api_endpoint),
            model=self,
            data={"size": size},
        )

        self._populate(result)

        return True

    def clone(self, label):
        """
        Clones this volume to a new volume in the same region with the given label

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-clone-volume

        :param label: The label for the new volume.
        :type label: str

        :returns: The new volume object.
        :rtype: Volume
        """
        result = self._client.post(
            "{}/clone".format(Volume.api_endpoint),
            model=self,
            data={"label": label},
        )

        if not "id" in result:
            raise UnexpectedResponseError("Unexpected response cloning volume!")

        return Volume(self._client, result["id"], result)

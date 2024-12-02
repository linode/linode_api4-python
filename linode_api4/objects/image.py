from dataclasses import dataclass
from typing import List, Optional, Union

from linode_api4.objects import Base, Property, Region
from linode_api4.objects.serializable import JSONObject, StrEnum


class ReplicationStatus(StrEnum):
    """
    The Enum class represents image replication status.
    """

    pending_replication = "pending replication"
    pending_deletion = "pending deletion"
    available = "available"
    creating = "creating"
    pending = "pending"
    replicating = "replicating"


@dataclass
class ImageRegion(JSONObject):
    """
    The region and status of an image replica.
    """

    include_none_values = True

    region: str = ""
    status: Optional[ReplicationStatus] = None


class Image(Base):
    """
    An Image is something a Linode Instance or Disk can be deployed from.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-image
    """

    api_endpoint = "/images/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True),
        "description": Property(mutable=True),
        "eol": Property(is_datetime=True),
        "expiry": Property(is_datetime=True),
        "status": Property(),
        "created": Property(is_datetime=True),
        "created_by": Property(),
        "updated": Property(is_datetime=True),
        "type": Property(),
        "is_public": Property(),
        "vendor": Property(),
        "size": Property(),
        "deprecated": Property(),
        "capabilities": Property(
            unordered=True,
        ),
        "tags": Property(mutable=True, unordered=True),
        "total_size": Property(),
        "regions": Property(json_object=ImageRegion, unordered=True),
    }

    def replicate(self, regions: Union[List[str], List[Region]]):
        """
        Replicate the image to other regions.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-replicate-image

        :param regions: A list of regions that the customer wants to replicate this image in.
                        At least one valid region is required and only core regions allowed.
                        Existing images in the regions not passed will be removed.
        :type regions: List[str]
        """
        params = {
            "regions": [
                region.id if isinstance(region, Region) else region
                for region in regions
            ]
        }

        result = self._client.post(
            "{}/regions".format(self.api_endpoint), model=self, data=params
        )

        # The replicate endpoint returns the updated Image, so we can use this
        # as an opportunity to refresh the object
        self._populate(result)

from dataclasses import dataclass
from typing import List

from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects.base import Base, JSONObject, Property
from linode_api4.objects.filtering import FilterableAttribute
from linode_api4.objects.serializable import JSONFilterableMetaclass


class Region(Base):
    """
    A Region. Regions correspond to individual data centers, each located in a different geographical area.

    API Documentation: https://www.linode.com/docs/api/regions/#region-view
    """

    api_endpoint = "/regions/{id}"
    properties = {
        "id": Property(identifier=True),
        "country": Property(),
        "capabilities": Property(),
        "status": Property(),
        "resolvers": Property(),
        "label": Property(),
    }

    @property
    def availability(self) -> List["RegionAvailabilityEntry"]:
        result = self._client.get(
            f"{self.api_endpoint}/availability", model=self
        )

        if result is None:
            raise UnexpectedResponseError(
                "Expected availability data, got None."
            )

        return [RegionAvailabilityEntry.from_json(v) for v in result]


@dataclass
class RegionAvailabilityEntry(JSONObject):
    """
    Represents the availability of a Linode type within a region.

    API Documentation: https://www.linode.com/docs/api/regions/#region-availability-view
    """

    region: str = None
    plan: str = None
    available: bool = False

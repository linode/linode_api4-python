from dataclasses import dataclass
from typing import List, Optional

from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects.base import Base, JSONObject, Property


@dataclass
class RegionPlacementGroupLimits(JSONObject):
    """
    Represents the Placement Group limits for the current account
    in a specific region.
    """

    maximum_pgs_per_customer: int = 0
    maximum_linodes_per_pg: int = 0


class Region(Base):
    """
    A Region. Regions correspond to individual data centers, each located in a different geographical area.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-region
    """

    api_endpoint = "/regions/{id}"
    properties = {
        "id": Property(identifier=True),
        "country": Property(),
        "capabilities": Property(unordered=True),
        "status": Property(),
        "resolvers": Property(),
        "label": Property(),
        "site_type": Property(),
        "placement_group_limits": Property(
            json_object=RegionPlacementGroupLimits
        ),
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

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-region-availability
    """

    region: Optional[str] = None
    plan: Optional[str] = None
    available: bool = False

from dataclasses import dataclass
from typing import List, Union

from linode_api4.objects.base import Base, Property
from linode_api4.objects.linode import Instance
from linode_api4.objects.region import Region
from linode_api4.objects.serializable import JSONObject, StrEnum


class PlacementGroupType(StrEnum):
    """
    An enum class that represents the available types of a Placement Group.
    """

    anti_affinity_local = "anti_affinity:local"


class PlacementGroupPolicy(StrEnum):
    """
    An enum class that represents the policy for Linode assignments to a Placement Group.
    """

    strict = "strict"
    flexible = "flexible"


@dataclass
class PlacementGroupMember(JSONObject):
    """
    Represents a member of a placement group.
    """

    linode_id: int = 0
    is_compliant: bool = False


class PlacementGroup(Base):
    """
    NOTE: Placement Groups may not currently be available to all users.

    A VM Placement Group, defining the affinity policy for Linodes
    created in a region.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-placement-group
    """

    api_endpoint = "/placement/groups/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True),
        "region": Property(slug_relationship=Region),
        "placement_group_type": Property(),
        "placement_group_policy": Property(),
        "is_compliant": Property(),
        "members": Property(json_object=PlacementGroupMember),
    }

    def assign(
        self,
        linodes: List[Union[Instance, int]],
        compliant_only: bool = False,
    ):
        """
        Assigns the specified Linodes to the Placement Group.

        :param linodes: A list of Linodes to assign to the Placement Group.
        :type linodes: List[Union[Instance, int]]
        """
        params = {
            "linodes": [
                v.id if isinstance(v, Instance) else v for v in linodes
            ],
            "compliant_only": compliant_only,
        }

        result = self._client.post(
            f"{PlacementGroup.api_endpoint}/assign", model=self, data=params
        )

        # The assign endpoint returns the updated PG, so we can use this
        # as an opportunity to refresh the object
        self._populate(result)

    def unassign(
        self,
        linodes: List[Union[Instance, int]],
    ):
        """
        Unassign the specified Linodes from the Placement Group.

        :param linodes: A list of Linodes to unassign from the Placement Group.
        :type linodes: List[Union[Instance, int]]
        """
        params = {
            "linodes": [
                v.id if isinstance(v, Instance) else v for v in linodes
            ],
        }

        result = self._client.post(
            f"{PlacementGroup.api_endpoint}/unassign", model=self, data=params
        )

        # The unassign endpoint returns the updated PG, so we can use this
        # as an opportunity to refresh the object
        self._populate(result)

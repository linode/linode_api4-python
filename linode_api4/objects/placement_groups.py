from dataclasses import dataclass
from typing import List, Union

from linode_api4.objects.base import Base, Property
from linode_api4.objects.linode import Instance
from linode_api4.objects.region import Region
from linode_api4.objects.serializable import JSONObject


@dataclass
class PlacementGroupMember(JSONObject):
    linode_id: int = 0
    is_compliant: bool = False


class PlacementGroup(Base):
    """
    A VM Placement Group.

    API Documentation: TODO
    """

    api_endpoint = "/placement/groups/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True),
        "region": Property(slug_relationship=Region),
        "affinity_type": Property(),
        "is_compliant": Property(),
        "is_strict": Property(),
        "members": Property(json_object=PlacementGroupMember),
    }

    def assign(
        self,
        linodes: List[Union[Instance, int]],
        compliant_only: bool = False,
    ):
        pass

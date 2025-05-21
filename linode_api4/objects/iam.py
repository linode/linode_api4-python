from __future__ import annotations

from dataclasses import dataclass
from typing import List

from linode_api4.objects.base import Base, JSONObject, Property


class LinodeEntity(Base):
    """
    An Entity represents an entity of the account.

    Currently the Entity can only be retrieved by listing, i.e.:
        entities = client.iam.entities()

    API documentation: TODO
    """

    properties = {
        "id": Property(identifier=True),
        "label": Property(),
        "type": Property(),
    }


@dataclass
class EntityAccess(JSONObject):
    """
    EntityAccess represents a user's access to an entity.
    """

    id: int
    type: str
    roles: List[str]

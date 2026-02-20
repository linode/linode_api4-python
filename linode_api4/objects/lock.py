from dataclasses import dataclass

from linode_api4.objects.base import Base, Property
from linode_api4.objects.serializable import JSONObject, StrEnum

__all__ = ["LockType", "LockEntity", "Lock"]


class LockType(StrEnum):
    """
    LockType defines valid values for resource lock types.

    API Documentation: TBD
    """

    cannot_delete = "cannot_delete"
    cannot_delete_with_subresources = "cannot_delete_with_subresources"


@dataclass
class LockEntity(JSONObject):
    """
    Represents the entity that is locked.

    API Documentation: TBD
    """

    id: int = 0
    type: str = ""
    label: str = ""
    url: str = ""


class Lock(Base):
    """
    A resource lock that prevents deletion or modification of a resource.

    API Documentation: TBD
    """

    api_endpoint = "/locks/{id}"

    properties = {
        "id": Property(identifier=True),
        "lock_type": Property(),
        "entity": Property(json_object=LockEntity),
    }

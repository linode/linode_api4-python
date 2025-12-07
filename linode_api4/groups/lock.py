from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import Lock, LockType

__all__ = ["LockGroup"]


class LockGroup(Group):
    """
    Encapsulates methods for interacting with Resource Locks.

    Resource locks prevent deletion or modification of resources.
    Currently, only Linode instances can be locked.
    """

    def __call__(self, *filters):
        """
        Returns a list of all Resource Locks on the account.

        This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           locks = client.locks()

        API Documentation: TBD

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Resource Locks on the account.
        :rtype: PaginatedList of Lock
        """
        return self.client._get_and_filter(Lock, *filters)

    def create(
        self,
        entity_type: str,
        entity_id: int | str,
        lock_type: LockType | str = LockType.cannot_delete,
    ) -> Lock:
        """
        Creates a new Resource Lock for the specified entity.

        API Documentation: TBD

        :param entity_type: The type of entity to lock (e.g., "linode").
        :type entity_type: str
        :param entity_id: The ID of the entity to lock.
        :type entity_id: int | str
        :param lock_type: The type of lock to create. Defaults to "cannot_delete".
        :type lock_type: LockType | str

        :returns: The newly created Resource Lock.
        :rtype: Lock
        """
        params = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "lock_type": lock_type,
        }

        result = self.client.post("/locks", data=params)

        if "id" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating lock!", json=result
            )

        return Lock(self.client, result["id"], result)

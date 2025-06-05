from typing import Any, Dict, List, Optional, Union

from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import EntityAccess, LinodeEntity


class IAMGroup(Group):
    def role_permissions(self):
        """
        Returns the permissions available on the account assigned to any user of the account.

        This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           permissions = client.role_permissions()

        API Documentation: TODO

        :returns: The JSON role permissions for the account.
        """
        return self.client.get("/iam/role-permissions", model=self)

    def role_permissions_user_get(self, username):
        """
        Returns the permissions available on the account assigned to the specified user.

        This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           permissions = client.role_permissions_user_get("myusername")

        API Documentation: TODO

        :returns: The JSON role permissions for the user.
        """
        return self.client.get(
            f"/iam/users/{username}/role-permissions", model=self
        )

    def role_permissions_user_set(
        self,
        username,
        account_access: Optional[List[str]] = None,
        entity_access: Optional[
            Union[List[EntityAccess], Dict[str, Any]]
        ] = None,
    ):
        """
        Assigns the specified permissions to the specified user, and returns them.

        This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           permissions = client.role_permissions_user_set("muusername")

        API Documentation: TODO

        :returns: The JSON role permissions for the user.
        """
        params = {
            "account_access": account_access,
            "entity_access": entity_access,
        }

        result = self.client.put(
            f"/iam/users/{username}/role-permissions",
            data=params,
        )

        if "account_access" not in result:
            raise UnexpectedResponseError(
                "Unexpected response updating role permissions!", json=result
            )

        return result

    def entities(self, *filters):
        """
        Returns the current entities of the account.

        This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           permissions = client.entities()

        API Documentation: TODO

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of entities that match the query.
        :rtype: PaginatedList of Entity
        """
        return self.client._get_and_filter(
            LinodeEntity, *filters, endpoint="/entities"
        )

from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import LongviewClient, LongviewSubscription


class LongviewGroup(Group):
    """
    Collections related to Linode Longview.
    """

    def clients(self, *filters):
        """
        Requests and returns a paginated list of LongviewClients on your
        account.

        API Documentation: https://www.linode.com/docs/api/longview/#longview-clients-list

        :param filters: Any number of filters to apply to this query.

        :returns: A list of Longview Clients matching the given filters.
        :rtype: PaginatedList of LongviewClient
        """
        return self.client._get_and_filter(LongviewClient, *filters)

    def client_create(self, label=None):
        """
        Creates a new LongviewClient, optionally with a given label.

        API Documentation: https://www.linode.com/docs/api/longview/#longview-client-create

        :param label: The label for the new client.  If None, a default label based
            on the new client's ID will be used.

        :returns: A new LongviewClient

        :raises ApiError: If a non-200 status code is returned
        :raises UnexpectedResponseError: If the returned data from the api does
            not look as expected.
        """
        result = self.client.post("/longview/clients", data={"label": label})

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating Longview Client!",
                json=result,
            )

        c = LongviewClient(self.client, result["id"], result)
        return c

    def subscriptions(self, *filters):
        """
        Requests and returns a paginated list of LongviewSubscriptions available

        API Documentation: https://www.linode.com/docs/api/longview/#longview-subscriptions-list

        :param filters: Any number of filters to apply to this query.

        :returns: A list of Longview Subscriptions matching the given filters.
        :rtype: PaginatedList of LongviewSubscription
        """
        return self.client._get_and_filter(LongviewSubscription, *filters)

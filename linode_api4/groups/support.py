from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import (
    VLAN,
    Database,
    Domain,
    Firewall,
    Instance,
    LKECluster,
    LongviewClient,
    NodeBalancer,
    SupportTicket,
    Volume,
)


class SupportGroup(Group):
    """
    Collections related to support tickets.
    """

    def tickets(self, *filters):
        """
        Returns a list of support tickets on this account.

        API Documentation: https://www.linode.com/docs/api/support/#support-tickets-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of support tickets on this account.
        :rtype: PaginatedList of SupportTicket
        """

        return self.client._get_and_filter(SupportTicket, *filters)

    def ticket_open(
        self,
        summary,
        description,
        managed_issue=False,
        regarding=None,
        **kwargs,
    ):
        """
        Opens a support ticket on this account.

        API Documentation: https://www.linode.com/docs/api/support/#support-ticket-open

        :param summary: The summary or title for this support ticket.
        :type summary: str
        :param description: The full details of the issue or question.
        :type description: str
        :param regarding: The resource being referred to in this ticket.
        :type regarding:
        :param managed_issue: Designates if this ticket relates to a managed service.
        :type managed_issue: bool

        :returns: The new support ticket.
        :rtype: SupportTicket
        """
        params = {
            "summary": summary,
            "description": description,
            "managed_issue": managed_issue,
        }

        type_to_id = {
            Instance: "linode_id",
            Domain: "domain_id",
            NodeBalancer: "nodebalancer_id",
            Volume: "volume_id",
            Firewall: "firewall_id",
            LKECluster: "lkecluster_id",
            Database: "database_id",
            LongviewClient: "longviewclient_id",
        }

        params.update(kwargs)

        if regarding:
            id_attr = type_to_id.get(type(regarding))

            if id_attr is not None:
                params[id_attr] = regarding.id
            elif isinstance(regarding, VLAN):
                params["vlan"] = regarding.label
                params["region"] = regarding.region
            else:
                raise ValueError(
                    "Cannot open ticket regarding type {}!".format(
                        type(regarding)
                    )
                )

        result = self.client.post("/support/tickets", data=params)

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating ticket!", json=result
            )

        t = SupportTicket(self.client, result["id"], result)
        return t

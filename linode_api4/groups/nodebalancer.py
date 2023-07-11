from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import Base, NodeBalancer


class NodeBalancerGroup(Group):
    def __call__(self, *filters):
        """
        Retrieves all of the NodeBalancers the acting user has access to.

        This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           nodebalancers = client.nodebalancers()

        API Documentation: https://www.linode.com/docs/api/nodebalancers/#nodebalancers-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of NodeBalancers the acting user can access.
        :rtype: PaginatedList of NodeBalancers
        """
        return self.client._get_and_filter(NodeBalancer, *filters)

    def create(self, region, **kwargs):
        """
        Creates a new NodeBalancer in the given Region.

        API Documentation: https://www.linode.com/docs/api/nodebalancers/#nodebalancer-create

        :param region: The Region in which to create the NodeBalancer.
        :type region: Region or str

        :returns: The new NodeBalancer
        :rtype: NodeBalancer
        """
        params = {
            "region": region.id if isinstance(region, Base) else region,
        }
        params.update(kwargs)

        result = self.client.post("/nodebalancers", data=params)

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating Nodebalaner!", json=result
            )

        n = NodeBalancer(self.client, result["id"], result)
        return n

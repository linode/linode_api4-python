from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import Base, NodeBalancer, NodeBalancerType


class NodeBalancerGroup(Group):
    def __call__(self, *filters):
        """
        Retrieves all of the NodeBalancers the acting user has access to.

        This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           nodebalancers = client.nodebalancers()

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-node-balancers

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

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-node-balancer

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

    def types(self, *filters):
        """
        Returns a :any:`PaginatedList` of :any:`NodeBalancerType` objects that represents a valid NodeBalancer type.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-node-balancer-types

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A Paginated List of NodeBalancer types that match the query.
        :rtype: PaginatedList of NodeBalancerType
        """

        return self.client._get_and_filter(
            NodeBalancerType, *filters, endpoint="/nodebalancers/types"
        )

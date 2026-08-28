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
        :param ipv4: A reserved IPv4 address to assign to this NodeBalancer.
                     NOTE: Reserved IP feature may not currently be available to all users.
        :type ipv4: str
        :param type: The NodeBalancer type. Supported values include
                     ``common``, ``basic``, ``premium``, ``premium_40g``,
                     and ``enterprise``. This cannot be changed after creation.
                     NOTE: Creating premium or enterprise NodeBalancers may not
                     currently be available to all users.
        :type type: str
        :param backend_connectivity: How this NodeBalancer communicates with
                     backends (``legacy``, ``ipv6``, or ``vpc``). If omitted,
                     the API infers a value from ``vpcs`` or config nodes, or
                     returns ``undefined`` until the first node is added.
                     ``undefined`` cannot be sent by clients. This cannot be
                     changed after creation.
                     NOTE: This field may not currently be available to all users.
        :type backend_connectivity: str
        :param vpcs: VPC attachments for this NodeBalancer. Required when
                     ``backend_connectivity`` is ``vpc``.
        :type vpcs: list[dict]
        :param configs: NodeBalancer configs and optional nodes to create
                     with this NodeBalancer. Node addresses must match the
                     selected or inferred backend connectivity.
        :type configs: list[dict]

        :returns: The new NodeBalancer
        :rtype: NodeBalancer
        """
        ipv4 = kwargs.pop("ipv4", None)
        params = {
            "region": region.id if isinstance(region, Base) else region,
        }
        if ipv4 is not None:
            params["ipv4"] = ipv4
        params.update(kwargs)

        result = self.client.post("/nodebalancers", data=params)

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating NodeBalancer!", json=result
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

from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import Base, KubeVersion, LKECluster


class LKEGroup(Group):
    """
    Encapsulates LKE-related methods of the :any:`LinodeClient`.  This
    should not be instantiated on its own, but should instead be used through
    an instance of :any:`LinodeClient`::

       client = LinodeClient(token)
       instances = client.lke.clusters() # use the LKEGroup

    This group contains all features beneath the `/lke` group in the API v4.
    """

    def versions(self, *filters):
        """
        Returns a :any:`PaginatedList` of :any:`KubeVersion` objects that can be
        used when creating an LKE Cluster.

        API Documentation: https://www.linode.com/docs/api/linode-kubernetes-engine-lke/#kubernetes-versions-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A Paginated List of kube versions that match the query.
        :rtype: PaginatedList of KubeVersion
        """
        return self.client._get_and_filter(KubeVersion, *filters)

    def clusters(self, *filters):
        """
        Returns a :any:`PaginagtedList` of :any:`LKECluster` objects that belong
        to this account.

        https://www.linode.com/docs/api/linode-kubernetes-engine-lke/#kubernetes-clusters-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A Paginated List of LKE clusters that match the query.
        :rtype: PaginatedList of LKECluster
        """
        return self.client._get_and_filter(LKECluster, *filters)

    def cluster_create(self, region, label, node_pools, kube_version, **kwargs):
        """
        Creates an :any:`LKECluster` on this account in the given region, with
        the given label, and with node pools as described.  For example::

           client = LinodeClient(TOKEN)

           # look up Region and Types to use.  In this example I'm just using
           # the first ones returned.
           target_region = client.regions().first()
           node_type = client.linode.types()[0]
           node_type_2 = client.linode.types()[1]
           kube_version = client.lke.versions()[0]

           new_cluster = client.lke.cluster_create(
               target_region,
               "example-cluster",
               [client.lke.node_pool(node_type, 3), client.lke.node_pool(node_type_2, 3)],
               kube_version
            )

        API Documentation: https://www.linode.com/docs/api/linode-kubernetes-engine-lke/#kubernetes-cluster-create

        :param region: The Region to create this LKE Cluster in.
        :type region: Region or str
        :param label: The label for the new LKE Cluster.
        :type label: str
        :param node_pools: The Node Pools to create.
        :type node_pools: one or a list of dicts containing keys "type" and "count".  See
                          :any:`node_pool` for a convenient way to create correctly-
                          formatted dicts.
        :param kube_version: The version of Kubernetes to use
        :type kube_version: KubeVersion or str
        :param kwargs: Any other arguments to pass along to the API.  See the API
                       docs for possible values.

        :returns: The new LKE Cluster
        :rtype: LKECluster
        """
        pools = []
        if not isinstance(node_pools, list):
            node_pools = [node_pools]

        for c in node_pools:
            if isinstance(c, dict):
                new_pool = {
                    "type": c["type"].id
                    if "type" in c and issubclass(type(c["type"]), Base)
                    else c.get("type"),
                    "count": c.get("count"),
                }

                pools += [new_pool]

        params = {
            "label": label,
            "region": region.id if issubclass(type(region), Base) else region,
            "node_pools": pools,
            "k8s_version": kube_version.id
            if issubclass(type(kube_version), Base)
            else kube_version,
        }
        params.update(kwargs)

        result = self.client.post("/lke/clusters", data=params)

        if "id" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating LKE cluster!", json=result
            )

        return LKECluster(self.client, result["id"], result)

    def node_pool(self, node_type, node_count):
        """
        Returns a dict that is suitable for passing into the `node_pools` array
        of :any:`cluster_create`.  This is a convenience method, and need not be
        used to create Node Pools.  For proper usage, see the docs for :any:`cluster_create`.

        :param node_type: The type of node to create in this node pool.
        :type node_type: Type or str
        :param node_count: The number of nodes to create in this node pool.
        :type node_count: int

        :returns: A dict describing the desired node pool.
        :rtype: dict
        """
        return {
            "type": node_type,
            "count": node_count,
        }

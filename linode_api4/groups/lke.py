from typing import Any, Dict, Optional, Union

from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.groups.lke_tier import LKETierGroup
from linode_api4.objects import (
    KubeVersion,
    LKECluster,
    LKEClusterControlPlaneOptions,
    LKEType,
    Type,
    drop_null_keys,
)
from linode_api4.objects.base import _flatten_request_body_recursive


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

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-lke-versions

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

        https://techdocs.akamai.com/linode-api/reference/get-lke-clusters

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A Paginated List of LKE clusters that match the query.
        :rtype: PaginatedList of LKECluster
        """
        return self.client._get_and_filter(LKECluster, *filters)

    def cluster_create(
        self,
        region,
        label,
        node_pools,
        kube_version,
        control_plane: Union[
            LKEClusterControlPlaneOptions, Dict[str, Any]
        ] = None,
        apl_enabled: bool = False,
        tier: Optional[str] = None,
        **kwargs,
    ):
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

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-lke-cluster

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
        :param control_plane: The control plane configuration of this LKE cluster.
        :type control_plane: Dict[str, Any] or LKEClusterControlPlaneRequest
        :param apl_enabled: Whether this cluster should use APL.
                            NOTE: This field is in beta and may only
                            function if base_url is set to `https://api.linode.com/v4beta`.
        :type apl_enabled: bool
        :param tier: The tier of LKE cluster to create.
                     NOTE: This field is in beta and may only
                     function if base_url is set to `https://api.linode.com/v4beta`.
        :type tier: str
        :param kwargs: Any other arguments to pass along to the API.  See the API
                       docs for possible values.

        :returns: The new LKE Cluster
        :rtype: LKECluster
        """

        params = {
            "label": label,
            "region": region,
            "k8s_version": kube_version,
            "node_pools": (
                node_pools if isinstance(node_pools, list) else [node_pools]
            ),
            "control_plane": control_plane,
            "tier": tier,
        }
        params.update(kwargs)

        # Prevent errors for users without access to APL
        if apl_enabled:
            params["apl_enabled"] = apl_enabled

        result = self.client.post(
            "/lke/clusters",
            data=drop_null_keys(_flatten_request_body_recursive(params)),
        )

        if "id" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating LKE cluster!", json=result
            )

        return LKECluster(self.client, result["id"], result)

    def node_pool(self, node_type: Union[Type, str], node_count: int, **kwargs):
        """
        Returns a dict that is suitable for passing into the `node_pools` array
        of :any:`cluster_create`.  This is a convenience method, and need not be
        used to create Node Pools.  For proper usage, see the docs for :any:`cluster_create`.

        :param node_type: The type of node to create in this node pool.
        :type node_type: Type or str
        :param node_count: The number of nodes to create in this node pool.
        :type node_count: int
        :param kwargs: Other attributes to create this node pool with.
        :type kwargs: Any

        :returns: A dict describing the desired node pool.
        :rtype: dict
        """
        result = {
            "type": node_type,
            "count": node_count,
        }

        result.update(kwargs)

        return result

    def types(self, *filters):
        """
        Returns a :any:`PaginatedList` of :any:`LKEType` objects that represents a valid LKE type.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-lke-types

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A Paginated List of LKE types that match the query.
        :rtype: PaginatedList of LKEType
        """

        return self.client._get_and_filter(
            LKEType, *filters, endpoint="/lke/types"
        )

    def tier(self, id: str) -> LKETierGroup:
        """
        Returns an object representing the LKE tier API path.

        NOTE: LKE tiers may not currently be available to all users.

        :param id: The ID of the tier.
        :type id: str

        :returns: An object representing the LKE tier API path.
        :rtype: LKETier
        """

        return LKETierGroup(self.client, id)

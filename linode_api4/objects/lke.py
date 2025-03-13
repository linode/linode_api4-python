from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from urllib import parse

from linode_api4.common import Price, RegionPrice
from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects import (
    Base,
    DerivedBase,
    Instance,
    JSONObject,
    MappedObject,
    Property,
    Region,
    Type,
)
from linode_api4.objects.base import _flatten_request_body_recursive
from linode_api4.util import drop_null_keys


class LKEType(Base):
    """
    An LKEType represents the structure of a valid LKE type.
    Currently the LKEType can only be retrieved by listing, i.e.:
        types = client.lke.types()

    API documentation: https://techdocs.akamai.com/linode-api/reference/get-lke-types
    """

    properties = {
        "id": Property(identifier=True),
        "label": Property(),
        "price": Property(json_object=Price),
        "region_prices": Property(json_object=RegionPrice),
        "transfer": Property(),
    }


class KubeVersion(Base):
    """
    A KubeVersion is a version of Kubernetes that can be deployed on LKE.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-lke-version
    """

    api_endpoint = "/lke/versions/{id}"

    properties = {
        "id": Property(identifier=True),
    }


class TieredKubeVersion(DerivedBase):
    """
    A TieredKubeVersion is a version of Kubernetes that is specific to a certain LKE tier.

    NOTE: LKE tiers may not currently be available to all users.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-lke-version
    """

    api_endpoint = "/lke/tiers/{tier}/versions/{id}"
    parent_id_name = "tier"
    id_attribute = "id"
    derived_url_path = "versions"

    properties = {
        "id": Property(identifier=True),
        "tier": Property(identifier=True),
    }


@dataclass
class LKENodePoolTaint(JSONObject):
    """
    LKENodePoolTaint represents the structure of a single taint that can be
    applied to a node pool.
    """

    include_none_values = True

    key: Optional[str] = None
    value: Optional[str] = None
    effect: Optional[str] = None


@dataclass
class LKEClusterControlPlaneACLAddressesOptions(JSONObject):
    """
    LKEClusterControlPlaneACLAddressesOptions are options used to configure
    IP ranges that are explicitly allowed to access an LKE cluster's control plane.
    """

    ipv4: Optional[List[str]] = None

    ipv6: Optional[List[str]] = None


@dataclass
class LKEClusterControlPlaneACLOptions(JSONObject):
    """
    LKEClusterControlPlaneACLOptions is used to set
    the ACL configuration of an LKE cluster's control plane.
    """

    enabled: Optional[bool] = None
    addresses: Optional[LKEClusterControlPlaneACLAddressesOptions] = None


@dataclass
class LKEClusterControlPlaneOptions(JSONObject):
    """
    LKEClusterControlPlaneOptions is used to configure
    the control plane of an LKE cluster during its creation.
    """

    high_availability: Optional[bool] = None
    acl: Optional[LKEClusterControlPlaneACLOptions] = None


@dataclass
class LKEClusterControlPlaneACLAddresses(JSONObject):
    """
    LKEClusterControlPlaneACLAddresses describes IP ranges that are explicitly allowed
    to access an LKE cluster's control plane.
    """

    include_none_values = True

    ipv4: Optional[List[str]] = None
    ipv6: Optional[List[str]] = None


@dataclass
class LKEClusterControlPlaneACL(JSONObject):
    """
    LKEClusterControlPlaneACL describes the ACL configuration of an LKE cluster's
    control plane.
    """

    include_none_values = True

    enabled: bool = False
    addresses: Optional[LKEClusterControlPlaneACLAddresses] = None


class LKENodePoolNode:
    """
    AN LKE Node Pool Node is a helper class that is used to populate the "nodes"
    array of an LKE Node Pool, and set up an automatic relationship with the
    Linode Instance the Node represented.
    """

    def __init__(self, client, json):
        """
        Creates this NodePoolNode
        """
        #: The ID of this Node Pool Node
        self.id = json.get(
            "id"
        )  # why do these have an ID if they don't have an endpoint of their own?

        #: The ID of the Linode Instance this Node represents
        self.instance_id = json.get("instance_id")

        #: The Instance object backing this Node Pool Node
        self.instance = Instance(client, self.instance_id)

        #: The Status of this Node Pool Node
        self.status = json.get("status")


class LKENodePool(DerivedBase):
    """
    An LKE Node Pool describes a pool of Linode Instances that exist within an
    LKE Cluster.

    NOTE: The k8s_version and update_strategy fields are only available for LKE Enterprise clusters.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-lke-node-pool
    """

    api_endpoint = "/lke/clusters/{cluster_id}/pools/{id}"
    derived_url_path = "pools"
    parent_id_name = "cluster_id"

    properties = {
        "id": Property(identifier=True),
        "cluster_id": Property(identifier=True),
        "type": Property(slug_relationship=Type),
        "disks": Property(),
        "disk_encryption": Property(),
        "count": Property(mutable=True),
        "nodes": Property(
            volatile=True
        ),  # this is formatted in _populate below
        "autoscaler": Property(mutable=True),
        "tags": Property(mutable=True, unordered=True),
        "labels": Property(mutable=True),
        "taints": Property(mutable=True),
        # Enterprise-specific properties
        # Ideally we would use slug_relationship=TieredKubeVersion here, but
        # it isn't possible without an extra request because the tier is not
        # directly exposed in the node pool response.
        "k8s_version": Property(mutable=True),
        "update_strategy": Property(mutable=True),
    }

    def _parse_raw_node(
        self, raw_node: Union[LKENodePoolNode, dict, str]
    ) -> LKENodePoolNode:
        """
        Builds a list of LKENodePoolNode objects given a node pool response's JSON.
        """
        if isinstance(raw_node, LKENodePoolNode):
            return raw_node

        if isinstance(raw_node, dict):
            node_id = raw_node.get("id")
            if node_id is None:
                raise ValueError("Node dictionary does not contain 'id' key")

            return LKENodePoolNode(self._client, raw_node)

        if isinstance(raw_node, str):
            return self._client.load(
                LKENodePoolNode, target_id=raw_node, target_parent_id=self.id
            )

        raise TypeError("Unsupported node type: {}".format(type(raw_node)))

    def _populate(self, json):
        """
        Parse Nodes into more useful LKENodePoolNode objects
        """

        if json is not None and json != {}:
            json["nodes"] = [
                self._parse_raw_node(node) for node in json.get("nodes", [])
            ]

            json["taints"] = [
                (
                    LKENodePoolTaint.from_json(taint)
                    if not isinstance(taint, LKENodePoolTaint)
                    else taint
                )
                for taint in json.get("taints", [])
            ]

        super()._populate(json)

    def recycle(self):
        """
        Deleted and recreates all Linodes in this Node Pool in a rolling fashion.
        Completing this operation may take several minutes.  This operation will
        cause all local data on Linode Instances in this pool to be lost.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-lke-cluster-pool-recycle
        """
        self._client.post(
            "{}/recycle".format(LKENodePool.api_endpoint), model=self
        )
        self.invalidate()


class LKECluster(Base):
    """
    An LKE Cluster is a single k8s cluster deployed via Linode Kubernetes Engine.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-lke-cluster
    """

    api_endpoint = "/lke/clusters/{id}"

    properties = {
        "id": Property(identifier=True),
        "created": Property(is_datetime=True),
        "label": Property(mutable=True),
        "tags": Property(mutable=True, unordered=True),
        "updated": Property(is_datetime=True),
        "region": Property(slug_relationship=Region),
        "k8s_version": Property(slug_relationship=KubeVersion, mutable=True),
        "pools": Property(derived_class=LKENodePool),
        "control_plane": Property(mutable=True),
        "apl_enabled": Property(),
        "tier": Property(),
    }

    def invalidate(self):
        """
        Extends the default invalidation logic to drop cached properties.
        """
        if hasattr(self, "_api_endpoints"):
            del self._api_endpoints

        if hasattr(self, "_kubeconfig"):
            del self._kubeconfig

        if hasattr(self, "_control_plane_acl"):
            del self._control_plane_acl

        Base.invalidate(self)

    @property
    def api_endpoints(self):
        """
        A list of API Endpoints for this Cluster.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-lke-cluster-api-endpoints

        :returns: A list of MappedObjects of the API Endpoints
        :rtype: List[MappedObject]
        """
        # This result appears to be a PaginatedList, but objects in the list don't
        # have IDs and can't be retrieved on their own, and it doesn't accept normal
        # pagination properties, so we're converting this to a list of strings.
        if not hasattr(self, "_api_endpoints"):
            results = self._client.get(
                "{}/api-endpoints".format(LKECluster.api_endpoint), model=self
            )

            self._api_endpoints = [MappedObject(**c) for c in results["data"]]

        return self._api_endpoints

    @property
    def kubeconfig(self):
        """
        The administrative Kubernetes Config used to access this cluster, encoded
        in base64.  Note that this config contains sensitive credentials to your
        cluster.

        To convert this config into a readable form, use python's `base64` module::

           import base64

           config = my_cluster.kubeconfig
           yaml_config = base64.b64decode(config)

           # write this config out to disk
           with open("/path/to/target/kubeconfig.yaml", "w") as f:
               f.write(yaml_config.decode())

        It may take a few minutes for a config to be ready when creating a new
        cluster; during that time this request may fail.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-lke-cluster-kubeconfig

        :returns: The Kubeconfig file for this Cluster.
        :rtype: str
        """
        if not hasattr(self, "_kubeconfig"):
            result = self._client.get(
                "{}/kubeconfig".format(LKECluster.api_endpoint), model=self
            )

            self._kubeconfig = result["kubeconfig"]

        return self._kubeconfig

    @property
    def control_plane_acl(self) -> LKEClusterControlPlaneACL:
        """
        Gets the ACL configuration of this cluster's control plane.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-lke-cluster-acl

        :returns: The cluster's control plane ACL configuration.
        :rtype: LKEClusterControlPlaneACL
        """

        if not hasattr(self, "_control_plane_acl"):
            result = self._client.get(
                f"{LKECluster.api_endpoint}/control_plane_acl", model=self
            )

            self._control_plane_acl = result.get("acl")

        return LKEClusterControlPlaneACL.from_json(self._control_plane_acl)

    @property
    def apl_console_url(self) -> Optional[str]:
        """
        Returns the URL of this cluster's APL installation if this cluster
        is APL-enabled, else None.

        :returns: The URL of the APL console for this cluster.
        :rtype: str or None
        """

        if not self.apl_enabled:
            return None

        return f"https://console.lke{self.id}.akamai-apl.net"

    @property
    def apl_health_check_url(self) -> Optional[str]:
        """
        Returns the URL of this cluster's APL health check endpoint if this cluster
        is APL-enabled, else None.

        :returns: The URL of the APL console for this cluster.
        :rtype: str or None
        """

        if not self.apl_enabled:
            return None

        return f"https://auth.lke{self.id}.akamai-apl.net/ready"

    def node_pool_create(
        self,
        node_type: Union[Type, str],
        node_count: int,
        labels: Optional[Dict[str, str]] = None,
        taints: List[Union[LKENodePoolTaint, Dict[str, Any]]] = None,
        k8s_version: Optional[
            Union[str, KubeVersion, TieredKubeVersion]
        ] = None,
        update_strategy: Optional[str] = None,
        **kwargs,
    ):
        """
        Creates a new :any:`LKENodePool` for this cluster.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-lke-cluster-pools

        :param node_type: The type of nodes to create in this pool.
        :type node_type: :any:`Type` or str
        :param node_count: The number of nodes to create in this pool.
        :type node_count: int
        :param labels: A dict mapping labels to their values to apply to this pool.
        :type labels: Dict[str, str]
        :param taints: A list of taints to apply to this pool.
        :type taints: List of :any:`LKENodePoolTaint` or dict.
        :param k8s_version: The Kubernetes version to use for this pool.
                            NOTE: This field is specific to enterprise clusters.
        :type k8s_version: str, KubeVersion, or TieredKubeVersion
        :param update_strategy: The strategy to use when updating this node pool.
                                NOTE: This field is specific to enterprise clusters.
        :type update_strategy: str
        :param kwargs: Any other arguments to pass to the API.  See the API docs
                       for possible values.

        :returns: The new Node Pool
        :rtype: LKENodePool
        """
        params = {
            "type": node_type,
            "count": node_count,
            "labels": labels,
            "taints": taints,
            "k8s_version": k8s_version,
            "update_strategy": update_strategy,
        }

        if labels is not None:
            params["labels"] = labels

        if taints is not None:
            params["taints"] = taints

        params.update(kwargs)

        result = self._client.post(
            "{}/pools".format(LKECluster.api_endpoint),
            model=self,
            data=drop_null_keys(_flatten_request_body_recursive(params)),
        )
        self.invalidate()

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response creating node pool!", json=result
            )

        return LKENodePool(self._client, result["id"], self.id, result)

    def cluster_dashboard_url_view(self):
        """
        Get a Kubernetes Dashboard access URL for this Cluster.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-lke-cluster-dashboard

        :returns: The Kubernetes Dashboard access URL for this Cluster.
        :rtype: str
        """

        result = self._client.get(
            "{}/dashboard".format(LKECluster.api_endpoint), model=self
        )

        return result["url"]

    def kubeconfig_delete(self):
        """
        Delete and regenerate the Kubeconfig file for a Cluster.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/delete-lke-cluster-kubeconfig
        """

        self._client.delete(
            "{}/kubeconfig".format(LKECluster.api_endpoint), model=self
        )

    def node_view(self, nodeId):
        """
        Get a specific Node by ID.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-lke-cluster-node

        :param nodeId: ID of the Node to look up.
        :type nodeId: str

        :returns: The specified Node
        :rtype: LKENodePoolNode
        """

        node = self._client.get(
            "{}/nodes/{}".format(
                LKECluster.api_endpoint, parse.quote(str(nodeId))
            ),
            model=self,
        )

        return LKENodePoolNode(self._client, node)

    def node_delete(self, nodeId):
        """
        Delete a specific Node from a Node Pool.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/delete-lke-cluster-node

        :param nodeId: ID of the Node to delete.
        :type nodeId: str
        """

        self._client.delete(
            "{}/nodes/{}".format(
                LKECluster.api_endpoint, parse.quote(str(nodeId))
            ),
            model=self,
        )

    def node_recycle(self, nodeId):
        """
        Recycle a specific Node from an LKE cluster.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-lke-cluster-node-recycle

        :param nodeId: ID of the Node to recycle.
        :type nodeId: str
        """

        self._client.post(
            "{}/nodes/{}/recycle".format(
                LKECluster.api_endpoint, parse.quote(str(nodeId))
            ),
            model=self,
        )

    def cluster_nodes_recycle(self):
        """
        Recycles all nodes in all pools of a designated Kubernetes Cluster.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-lke-cluster-recycle
        """

        self._client.post(
            "{}/recycle".format(LKECluster.api_endpoint), model=self
        )

    def cluster_regenerate(self):
        """
        Regenerate the Kubeconfig file and/or the service account token for a Cluster.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-lke-cluster-regenerate
        """

        self._client.post(
            "{}/regenerate".format(LKECluster.api_endpoint), model=self
        )

    def service_token_delete(self):
        """
        Delete and regenerate the service account token for a Cluster.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/delete-lke-service-token
        """

        self._client.delete(
            "{}/servicetoken".format(LKECluster.api_endpoint), model=self
        )

    def control_plane_acl_update(
        self, acl: Union[LKEClusterControlPlaneACLOptions, Dict[str, Any]]
    ) -> LKEClusterControlPlaneACL:
        """
        Updates the ACL configuration for this cluster's control plane.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/put-lke-cluster-acl

        :param acl: The ACL configuration to apply to this cluster.
        :type acl: LKEClusterControlPlaneACLOptions or Dict[str, Any]

        :returns: The updated control plane ACL configuration.
        :rtype: LKEClusterControlPlaneACL
        """
        if isinstance(acl, LKEClusterControlPlaneACLOptions):
            acl = acl.dict

        result = self._client.put(
            f"{LKECluster.api_endpoint}/control_plane_acl",
            model=self,
            data={"acl": drop_null_keys(acl)},
        )

        acl = result.get("acl")

        self._control_plane_acl = result.get("acl")

        return LKEClusterControlPlaneACL.from_json(acl)

    def control_plane_acl_delete(self):
        """
        Deletes the ACL configuration for this cluster's control plane.
        This has the same effect as calling control_plane_acl_update with the `enabled` field
        set to False. Access controls are disabled and all rules are deleted.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/delete-lke-cluster-acl
        """
        self._client.delete(
            f"{LKECluster.api_endpoint}/control_plane_acl", model=self
        )

        # Invalidate the cache so it is automatically refreshed on next access
        if hasattr(self, "_control_plane_acl"):
            del self._control_plane_acl

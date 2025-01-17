import os
from urllib import parse

from linode_api4.common import Price, RegionPrice
from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects.base import Base, MappedObject, Property
from linode_api4.objects.dbase import DerivedBase
from linode_api4.objects.networking import Firewall, IPAddress
from linode_api4.objects.region import Region


class NodeBalancerType(Base):
    """
    An NodeBalancerType represents the structure of a valid NodeBalancer type.
    Currently the NodeBalancerType can only be retrieved by listing, i.e.:
        types = client.nodebalancers.types()

    API documentation: https://techdocs.akamai.com/linode-api/reference/get-node-balancer-types
    """

    properties = {
        "id": Property(identifier=True),
        "label": Property(),
        "price": Property(json_object=Price),
        "region_prices": Property(json_object=RegionPrice),
        "transfer": Property(),
    }


class NodeBalancerNode(DerivedBase):
    """
    The information about a single Node, a backend for this NodeBalancer’s configured port.

    API documentation: https://techdocs.akamai.com/linode-api/reference/get-node-balancer-node
    """

    api_endpoint = (
        "/nodebalancers/{nodebalancer_id}/configs/{config_id}/nodes/{id}"
    )
    derived_url_path = "nodes"
    parent_id_name = "config_id"

    properties = {
        "id": Property(identifier=True),
        "config_id": Property(identifier=True),
        "nodebalancer_id": Property(identifier=True),
        "label": Property(mutable=True),
        "address": Property(mutable=True),
        "weight": Property(mutable=True),
        "mode": Property(mutable=True),
        "status": Property(),
        "tags": Property(mutable=True, unordered=True),
    }

    def __init__(self, client, id, parent_id, nodebalancer_id=None, json=None):
        """
        We need a special constructor here because this object's parent
        has a parent itself.
        """
        if not nodebalancer_id and not isinstance(parent_id, tuple):
            raise ValueError(
                "NodeBalancerNode must either be created with a nodebalancer_id or a tuple of "
                "(config_id, nodebalancer_id) for parent_id!"
            )

        if isinstance(parent_id, tuple):
            nodebalancer_id = parent_id[1]
            parent_id = parent_id[0]

        DerivedBase.__init__(self, client, id, parent_id, json=json)

        self._set("nodebalancer_id", nodebalancer_id)


class NodeBalancerConfig(DerivedBase):
    """
    The configuration information for a single port of this NodeBalancer.

    API documentation: https://techdocs.akamai.com/linode-api/reference/get-node-balancer-config
    """

    api_endpoint = "/nodebalancers/{nodebalancer_id}/configs/{id}"
    derived_url_path = "configs"
    parent_id_name = "nodebalancer_id"

    properties = {
        "id": Property(identifier=True),
        "nodebalancer_id": Property(identifier=True),
        "port": Property(mutable=True),
        "protocol": Property(mutable=True),
        "algorithm": Property(mutable=True),
        "stickiness": Property(mutable=True),
        "check": Property(mutable=True),
        "check_interval": Property(mutable=True),
        "check_timeout": Property(mutable=True),
        "check_attempts": Property(mutable=True),
        "check_path": Property(mutable=True),
        "check_body": Property(mutable=True),
        "check_passive": Property(mutable=True),
        "udp_check_port": Property(mutable=True),
        "udp_session_timeout": Property(),
        "ssl_cert": Property(mutable=True),
        "ssl_key": Property(mutable=True),
        "ssl_commonname": Property(),
        "ssl_fingerprint": Property(),
        "cipher_suite": Property(mutable=True),
        "nodes_status": Property(),
        "proxy_protocol": Property(mutable=True),
    }

    def save(self, force=True) -> bool:
        """
        Send this NodeBalancerConfig's mutable values to the server in a PUT request.
        :param force: If true, this method will always send a PUT request regardless of
                      whether the field has been explicitly updated. For optimization
                      purposes, this field should be set to false for typical update
                      operations. (Defaults to True)
        :type force: bool
        """

        if not force and not self._changed:
            return False

        data = self._serialize()

        print(data)

        if data.get("protocol") == "udp" and "cipher_suite" in data:
            data.pop("cipher_suite")

        print(data)

        result = self._client.put(
            NodeBalancerConfig.api_endpoint, model=self, data=data
        )

        if "error" in result:
            return False

        self._populate(result)

        return True

    @property
    def nodes(self):
        """
        This is a special derived_class relationship because NodeBalancerNode is the
        only api object that requires two parent_ids

        Returns a paginated list of NodeBalancer nodes associated with this Config.
        These are the backends that will be sent traffic for this port.

        API documentation: https://techdocs.akamai.com/linode-api/reference/get-node-balancer-config-nodes

        :returns: A paginated list of NodeBalancer nodes.
        :rtype: PaginatedList of NodeBalancerNode
        """
        if not hasattr(self, "_nodes"):
            base_url = "{}/{}".format(
                NodeBalancerConfig.api_endpoint,
                NodeBalancerNode.derived_url_path,
            )
            result = self._client._get_objects(
                base_url,
                NodeBalancerNode,
                model=self,
                parent_id=(self.id, self.nodebalancer_id),
            )

            self._set("_nodes", result)

        return self._nodes

    def node_create(self, label, address, **kwargs):
        """
        Creates a NodeBalancer Node, a backend that can accept traffic for this
        NodeBalancer Config. Nodes are routed requests on the configured port based
        on their status.

        API documentation: https://techdocs.akamai.com/linode-api/reference/post-node-balancer-node

        :param address: The private IP Address where this backend can be reached.
                        This must be a private IP address.
        :type address: str

        :param label: The label for this node. This is for display purposes only.
                      Must have a length between 2 and 32 characters.
        :type label: str

        :returns: The node which is created successfully.
        :rtype: NodeBalancerNode
        """
        params = {
            "label": label,
            "address": address,
        }
        params.update(kwargs)

        result = self._client.post(
            "{}/nodes".format(NodeBalancerConfig.api_endpoint),
            model=self,
            data=params,
        )
        self.invalidate()

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response creating node!", json=result
            )

        # this is three levels deep, so we need a special constructor
        n = NodeBalancerNode(
            self._client, result["id"], self.id, self.nodebalancer_id, result
        )
        return n

    def load_ssl_data(self, cert_file, key_file):
        """
        A convenience method that loads a cert and a key from files and sets them
        on this object.  This can make enabling ssl easier (instead of you needing
        to load the files yourself).

        This does *not* change protocol/port for you, or save anything.  Once this
        is called, you must still call `save()` on this object for the changes to
        take effect.

        :param cert_file: A path to the file containing the public certificate
        :type cert_file: str
        :param key_file: A path to the file containing the unpassphrased private key
        :type key_file: str
        """
        # access a server-loaded field to ensure this object is loaded from the
        # server before setting values.  Failing to do this can cause an unloaded
        # object to overwrite these values on a subsequent load, which happens to
        # occur on a save()
        _ = self.ssl_fingerprint

        # we're disabling warnings here because these attributes are defined dynamically
        # through linode.objects.Base, and pylint isn't privy
        if os.path.isfile(os.path.expanduser(cert_file)):
            with open(os.path.expanduser(cert_file)) as f:
                self.ssl_cert = f.read()

        if os.path.isfile(os.path.expanduser(key_file)):
            with open(os.path.expanduser(key_file)) as f:
                self.ssl_key = f.read()


class NodeBalancer(Base):
    """
    A single NodeBalancer you can access.

    API documentation: https://techdocs.akamai.com/linode-api/reference/get-node-balancer
    """

    api_endpoint = "/nodebalancers/{id}"
    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True),
        "hostname": Property(),
        "client_conn_throttle": Property(mutable=True),
        "status": Property(),
        "created": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
        "ipv4": Property(relationship=IPAddress),
        "ipv6": Property(),
        "region": Property(slug_relationship=Region),
        "configs": Property(derived_class=NodeBalancerConfig),
        "transfer": Property(),
        "tags": Property(mutable=True, unordered=True),
        "client_udp_sess_throttle": Property(mutable=True),
    }

    # create derived objects
    def config_create(self, **kwargs):
        """
        Creates a NodeBalancer Config, which allows the NodeBalancer to accept traffic
        on a new port. You will need to add NodeBalancer Nodes to the new Config before
        it can actually serve requests.

        API documentation: https://techdocs.akamai.com/linode-api/reference/post-node-balancer-config

        :returns: The config that created successfully.
        :rtype: NodeBalancerConfig
        """
        params = kwargs

        result = self._client.post(
            "{}/configs".format(NodeBalancer.api_endpoint),
            model=self,
            data=params,
        )
        self.invalidate()

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response creating config!", json=result
            )

        c = NodeBalancerConfig(self._client, result["id"], self.id, result)
        return c

    def config_rebuild(self, config_id, nodes, **kwargs):
        """
        Rebuilds a NodeBalancer Config and its Nodes that you have permission to modify.
        Use this command to update a NodeBalancer’s Config and Nodes with a single request.

        API documentation: https://techdocs.akamai.com/linode-api/reference/post-rebuild-node-balancer-config

        :param config_id: The ID of the Config to access.
        :type config_id: int

        :param nodes: The NodeBalancer Node(s) that serve this Config.
        :type nodes: [{ address: str, id: int, label: str, mode: str, weight: int }]

        :returns: A nodebalancer config that rebuilt successfully.
        :rtype: NodeBalancerConfig
        """
        params = {
            "nodes": nodes,
        }
        params.update(kwargs)

        result = self._client.post(
            "{}/configs/{}/rebuild".format(
                NodeBalancer.api_endpoint, parse.quote(str(config_id))
            ),
            model=self,
            data=params,
        )

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response rebuilding config!", json=result
            )

        return NodeBalancerConfig(self._client, result["id"], self.id, result)

    def statistics(self):
        """
        Returns detailed statistics about the requested NodeBalancer.

        API documentation: https://techdocs.akamai.com/linode-api/reference/get-node-balancer-stats

        :returns: The requested stats.
        :rtype: MappedObject
        """
        result = self._client.get(
            "{}/stats".format(NodeBalancer.api_endpoint), model=self
        )

        if not "title" in result:
            raise UnexpectedResponseError(
                "Unexpected response generating stats!", json=result
            )
        return MappedObject(**result)

    def firewalls(self):
        """
        View Firewall information for Firewalls associated with this NodeBalancer.

        API Documentation: https://www.linode.com/docs/api/nodebalancers/#nodebalancer-firewalls-list

        :returns: A List of Firewalls of the Linode NodeBalancer.
        :rtype: List[Firewall]
        """
        result = self._client.get(
            "{}/firewalls".format(NodeBalancer.api_endpoint), model=self
        )

        return [
            Firewall(self._client, firewall["id"])
            for firewall in result["data"]
        ]

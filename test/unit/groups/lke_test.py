from test.unit.base import ClientBaseCase

from linode_api4.objects import (
    LKEClusterControlPlaneACLAddressesOptions,
    LKEClusterControlPlaneACLOptions,
    LKEClusterControlPlaneOptions,
)


class LKETest(ClientBaseCase):
    """
    Tests methods of the LKE class
    """

    def test_cluster_create_with_acl(self):
        """
        Tests that an LKE cluster can be created with a control plane ACL configuration.
        """

        with self.mock_post("lke/clusters") as m:
            self.client.lke.cluster_create(
                "us-mia",
                "test-acl-cluster",
                "1.29",
                [self.client.lke.node_pool("g6-nanode-1", 3)],
                control_plane=LKEClusterControlPlaneOptions(
                    acl=LKEClusterControlPlaneACLOptions(
                        enabled=True,
                        addresses=LKEClusterControlPlaneACLAddressesOptions(
                            ipv4=["10.0.0.1/32"], ipv6=["1234::5678"]
                        ),
                    )
                ),
            )

            assert "high_availability" not in m.call_data["control_plane"]
            assert m.call_data["control_plane"]["acl"]["enabled"]
            assert m.call_data["control_plane"]["acl"]["addresses"]["ipv4"] == [
                "10.0.0.1/32"
            ]
            assert m.call_data["control_plane"]["acl"]["addresses"]["ipv6"] == [
                "1234::5678"
            ]

    def test_cluster_create_enterprise_without_node_pools(self):
        """
        Tests that an enterprise LKE cluster can be created without node pools.
        """
        with self.mock_post("lke/clusters") as m:
            self.client.lke.cluster_create(
                "us-west",
                "test-enterprise-cluster",
                "1.29",
                tier="enterprise",
            )

            assert m.call_data["region"] == "us-west"
            assert m.call_data["label"] == "test-enterprise-cluster"
            assert m.call_data["k8s_version"] == "1.29"
            assert m.call_data["tier"] == "enterprise"
            assert m.call_data["node_pools"] == []

    def test_cluster_create_enterprise_case_insensitive(self):
        """
        Tests that tier comparison is case-insensitive for enterprise tier.
        """
        with self.mock_post("lke/clusters") as m:
            self.client.lke.cluster_create(
                "us-west",
                "test-enterprise-cluster",
                "1.29",
                tier="ENTERPRISE",
            )

            assert m.call_data["tier"] == "ENTERPRISE"
            assert m.call_data["node_pools"] == []

    def test_cluster_create_standard_without_node_pools_raises_error(self):
        """
        Tests that creating a standard LKE cluster without node pools raises ValueError.
        """
        with self.assertRaises(ValueError) as context:
            self.client.lke.cluster_create(
                "us-east",
                "test-standard-cluster",
                "1.29",
                tier="standard",
            )

        self.assertIn(
            "LKE standard clusters must have at least one node pool",
            str(context.exception),
        )

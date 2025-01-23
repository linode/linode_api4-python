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
                [self.client.lke.node_pool("g6-nanode-1", 3)],
                "1.29",
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

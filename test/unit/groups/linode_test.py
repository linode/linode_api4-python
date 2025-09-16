from test.unit.base import ClientBaseCase
from test.unit.objects.linode_interface_test import (
    build_interface_options_public,
    build_interface_options_vlan,
    build_interface_options_vpc,
)

from linode_api4 import (
    InstancePlacementGroupAssignment,
    InterfaceGeneration,
)
from linode_api4.objects import ConfigInterface


class LinodeTest(ClientBaseCase):
    """
    Tests methods of the Linode class
    """

    def test_instance_create_with_user_data(self):
        """
        Tests that the metadata field is populated on Linode create.
        """

        with self.mock_post("linode/instances/123") as m:
            self.client.linode.instance_create(
                "g6-nanode-1",
                "us-southeast",
                metadata=self.client.linode.build_instance_metadata(
                    user_data="cool"
                ),
            )

            self.assertEqual(
                m.call_data,
                {
                    "region": "us-southeast",
                    "type": "g6-nanode-1",
                    "metadata": {"user_data": "Y29vbA=="},
                },
            )

    def test_instance_create_with_interfaces_legacy(self):
        """
        Tests that user can pass a list of interfaces on Linode create.
        """
        interfaces = [
            {"purpose": "public"},
            ConfigInterface(
                purpose="vlan", label="cool-vlan", ipam_address="10.0.0.4/32"
            ),
        ]
        with self.mock_post("linode/instances/123") as m:
            self.client.linode.instance_create(
                "us-southeast",
                "g6-nanode-1",
                interface_generation=InterfaceGeneration.LEGACY_CONFIG,
                interfaces=interfaces,
            )

            self.assertEqual(
                m.call_data["interfaces"],
                [
                    {"purpose": "public"},
                    {
                        "purpose": "vlan",
                        "label": "cool-vlan",
                        "ipam_address": "10.0.0.4/32",
                    },
                ],
            )

    def test_build_instance_metadata(self):
        """
        Tests that the metadata field is built correctly.
        """
        self.assertEqual(
            self.client.linode.build_instance_metadata(user_data="cool"),
            {"user_data": "Y29vbA=="},
        )

        self.assertEqual(
            self.client.linode.build_instance_metadata(
                user_data="cool", encode_user_data=False
            ),
            {"user_data": "cool"},
        )

    def test_create_with_placement_group(self):
        """
        Tests that you can create a Linode with a Placement Group
        """

        with self.mock_post("linode/instances/123") as m:
            self.client.linode.instance_create(
                "g6-nanode-1",
                "eu-west",
                placement_group=InstancePlacementGroupAssignment(
                    id=123,
                    compliant_only=True,
                ),
            )

        self.assertEqual(
            m.call_data["placement_group"], {"id": 123, "compliant_only": True}
        )

    def test_instance_create_with_interfaces_linode(self):
        """
        Tests that a Linode can be created alongside multiple LinodeInterfaces.
        """

        interfaces = [
            build_interface_options_public(),
            build_interface_options_vpc(),
            build_interface_options_vlan(),
        ]

        with self.mock_post("linode/instances/124") as m:
            self.client.linode.instance_create(
                "g6-nanode-1",
                "us-mia",
                interface_generation=InterfaceGeneration.LINODE,
                interfaces=interfaces,
            )

            assert m.call_data == {
                "region": "us-mia",
                "type": "g6-nanode-1",
                "interface_generation": "linode",
                "interfaces": [iface._serialize() for iface in interfaces],
            }

    def test_create_with_maintenance_policy(self):
        """
        Tests that you can create a Linode with a maintenance policy
        """

        with self.mock_post("linode/instances/123") as m:
            self.client.linode.instance_create(
                "g6-nanode-1",
                "eu-west",
                maintenance_policy="linode/migrate",
            )

        self.assertEqual(m.call_data["maintenance_policy"], "linode/migrate")


class TypeTest(ClientBaseCase):
    def test_get_types(self):
        """
        Tests that Linode types can be returned
        """
        types = self.client.linode.types()

        self.assertEqual(len(types), 5)
        for t in types:
            self.assertTrue(t._populated)
            self.assertIsNotNone(t.id)
            self.assertIsNotNone(t.label)
            self.assertIsNotNone(t.disk)
            self.assertIsNotNone(t.type_class)
            self.assertIsNotNone(t.gpus)
            self.assertIsNone(t.successor)
            self.assertIsNotNone(t.region_prices)
            self.assertIsNotNone(t.addons.backups.region_prices)
            self.assertIsNotNone(t.accelerated_devices)

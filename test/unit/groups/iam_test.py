import logging
from test.unit.base import ClientBaseCase

logger = logging.getLogger(__name__)


class IAMTest(ClientBaseCase):
    """
    Tests methods of the IAMGroup class
    """

    def test_entities(self):
        """
        Test that entities can be properly retrieved
        """
        entities = self.client.iam.entities()

        self.assertEqual(len(entities), 14)

        self.assertEqual(entities[0].id, 7)
        self.assertEqual(entities[0].label, "linode7")
        self.assertEqual(entities[0].type, "linode")

        self.assertEqual(entities[1].id, 10)
        self.assertEqual(entities[1].label, "linode10")
        self.assertEqual(entities[1].type, "linode")

        self.assertEqual(entities[2].id, 1)
        self.assertEqual(entities[2].label, "no_devices")
        self.assertEqual(entities[2].type, "firewall")

        self.assertEqual(entities[3].id, 2)
        self.assertEqual(entities[3].label, "active_with_nodebalancer")
        self.assertEqual(entities[3].type, "firewall")

        self.assertEqual(entities[4].id, 1)
        self.assertEqual(entities[4].label, "nodebalancer-active")
        self.assertEqual(entities[4].type, "nodebalancer")

        self.assertEqual(entities[5].id, 1)
        self.assertEqual(entities[5].label, "active")
        self.assertEqual(entities[5].type, "longview")

        self.assertEqual(entities[6].id, 3)
        self.assertEqual(entities[6].label, "LongviewClientTest")
        self.assertEqual(entities[6].type, "longview")

        self.assertEqual(entities[7].id, 1)
        self.assertEqual(entities[7].label, "linDomTest1.com")
        self.assertEqual(entities[7].type, "domain")

        self.assertEqual(entities[8].id, 1)
        self.assertEqual(entities[8].label, "API Test")
        self.assertEqual(entities[8].type, "stackscript")

        self.assertEqual(entities[9].id, 1)
        self.assertEqual(entities[9].label, "Test image - mine")
        self.assertEqual(entities[9].type, "image")

        self.assertEqual(entities[10].id, 3)
        self.assertEqual(entities[10].label, "Test image - mine - creating")
        self.assertEqual(entities[10].type, "image")

        self.assertEqual(entities[11].id, 1)
        self.assertEqual(entities[11].label, "volume1")
        self.assertEqual(entities[11].type, "volume")

        self.assertEqual(entities[12].id, 1)
        self.assertEqual(entities[12].label, "mongo_cluster")
        self.assertEqual(entities[12].type, "database")

        self.assertEqual(entities[13].id, 3)
        self.assertEqual(entities[13].label, "empty-vpc")
        self.assertEqual(entities[13].type, "vpc")

    def test_role_permissions(self):
        """
        Test that account role permissions can be properly retrieved
        """
        role_permissions = self.client.iam.role_permissions()

        self.assertEqual(len(role_permissions["account_access"]), 3)
        self.assertEqual(len(role_permissions["entity_access"]), 2)

        self.assertEqual(
            role_permissions["account_access"][0]["type"], "account"
        )
        self.assertEqual(len(role_permissions["account_access"][0]["roles"]), 1)
        self.assertEqual(
            role_permissions["account_access"][0]["roles"][0]["name"],
            "account_admin",
        )
        self.assertEqual(
            role_permissions["account_access"][0]["roles"][0]["description"],
            "Access to perform any supported action on all entities of the account",
        )
        self.assertCountEqual(
            role_permissions["account_access"][0]["roles"][0]["permissions"],
            ["create_linode", "update_linode", "update_firewall"],
        )

        self.assertEqual(
            role_permissions["account_access"][1]["type"], "linode"
        )
        self.assertEqual(len(role_permissions["account_access"][1]["roles"]), 1)
        self.assertEqual(
            role_permissions["account_access"][1]["roles"][0]["name"],
            "account_linode_admin",
        )
        self.assertEqual(
            role_permissions["account_access"][1]["roles"][0]["description"],
            "Access to perform any supported action on all linode instances of the account",
        )
        self.assertCountEqual(
            role_permissions["account_access"][1]["roles"][0]["permissions"],
            ["create_linode", "update_linode", "delete_linode"],
        )

        self.assertEqual(
            role_permissions["account_access"][2]["type"], "firewall"
        )
        self.assertEqual(len(role_permissions["account_access"][2]["roles"]), 1)
        self.assertEqual(
            role_permissions["account_access"][2]["roles"][0]["name"],
            "firewall_creator",
        )
        self.assertEqual(
            role_permissions["account_access"][2]["roles"][0]["description"],
            "Access to create a firewall instance",
        )
        self.assertCountEqual(
            role_permissions["account_access"][2]["roles"][0]["permissions"],
            ["update_linode", "view_linode"],
        )

        self.assertEqual(role_permissions["entity_access"][0]["type"], "linode")
        self.assertEqual(len(role_permissions["entity_access"][0]["roles"]), 1)
        self.assertEqual(
            role_permissions["entity_access"][0]["roles"][0]["name"],
            "linode_contributor",
        )
        self.assertEqual(
            role_permissions["entity_access"][0]["roles"][0]["description"],
            "Access to update a linode instance",
        )
        self.assertCountEqual(
            role_permissions["entity_access"][0]["roles"][0]["permissions"],
            ["update_linode", "view_linode"],
        )

        self.assertEqual(
            role_permissions["entity_access"][1]["type"], "firewall"
        )
        self.assertEqual(len(role_permissions["entity_access"][1]["roles"]), 2)
        self.assertEqual(
            role_permissions["entity_access"][1]["roles"][0]["name"],
            "firewall_viewer",
        )
        self.assertEqual(
            role_permissions["entity_access"][1]["roles"][0]["description"],
            "Access to view a firewall instance",
        )
        self.assertCountEqual(
            role_permissions["entity_access"][1]["roles"][0]["permissions"],
            ["update_linode", "view_linode"],
        )
        self.assertEqual(
            role_permissions["entity_access"][1]["roles"][1]["name"],
            "firewall_admin",
        )
        self.assertEqual(
            role_permissions["entity_access"][1]["roles"][1]["description"],
            "Access to perform any supported action on a firewall instance",
        )
        self.assertCountEqual(
            role_permissions["entity_access"][1]["roles"][1]["permissions"],
            ["update_linode", "view_linode"],
        )

    def test_role_permissions_user_get(self):
        """
        Test that user role permissions can be properly retrieved
        """
        permissions = self.client.iam.role_permissions_user_get("myusername")

        self.assertIn("account_linode_admin", permissions["account_access"])
        self.assertIn("linode_creator", permissions["account_access"])
        self.assertIn("firewall_creator", permissions["account_access"])
        self.assertEqual(len(permissions["account_access"]), 3)

        self.assertEqual(len(permissions["entity_access"]), 2)

        self.assertEqual(permissions["entity_access"][0]["id"], 1)
        self.assertEqual(permissions["entity_access"][0]["type"], "linode")
        self.assertEqual(
            permissions["entity_access"][0]["roles"], ["linode_contributor"]
        )

        self.assertEqual(permissions["entity_access"][1]["id"], 1)
        self.assertEqual(permissions["entity_access"][1]["type"], "firewall")
        self.assertEqual(
            permissions["entity_access"][1]["roles"], ["firewall_admin"]
        )

    def test_role_permissions_user_set(self):
        with self.mock_put("/iam/users/myusername/role-permissions") as m:
            self.client.iam.role_permissions_user_set(
                "myusername",
                ["account_linode_admin", "linode_creator", "firewall_creator"],
                [
                    {
                        "id": 1,
                        "type": "linode",
                        "roles": ["linode_contributor"],
                    },
                    {"id": 1, "type": "firewall", "roles": ["firewall_admin"]},
                ],
            )

        self.assertEqual(m.method, "put")
        self.assertEqual(m.call_url, "/iam/users/myusername/role-permissions")

        self.assertIn("account_access", m.call_data)
        self.assertEqual(
            m.call_data["account_access"],
            ["account_linode_admin", "linode_creator", "firewall_creator"],
        )

        self.assertIn("entity_access", m.call_data)
        self.assertEqual(len(m.call_data["entity_access"]), 2)

        self.assertEqual(m.call_data["entity_access"][0]["id"], 1)
        self.assertEqual(m.call_data["entity_access"][0]["type"], "linode")
        self.assertEqual(
            m.call_data["entity_access"][0]["roles"], ["linode_contributor"]
        )

        self.assertEqual(m.call_data["entity_access"][1]["id"], 1)
        self.assertEqual(m.call_data["entity_access"][1]["type"], "firewall")
        self.assertEqual(
            m.call_data["entity_access"][1]["roles"], ["firewall_admin"]
        )

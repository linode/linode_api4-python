from test.unit.base import ClientBaseCase, MethodMock

from linode_api4 import VLAN, ExplicitNullValue, Instance, Region
from linode_api4.objects import Firewall, IPAddress, IPv6Range
from linode_api4.objects.networking import (
    ReservedIPAddress,
    ReservedIPAssignedEntity,
)


class NetworkingTest(ClientBaseCase):
    """
    Tests methods of the Networking class
    """

    def test_get_ipv6_range(self):
        """
        Tests that the IPv6Range object is properly generated.
        """

        ipv6Range = IPv6Range(self.client, "2600:3c01::")
        ipv6Range._api_get()

        self.assertEqual(ipv6Range.range, "2600:3c01::")
        self.assertEqual(ipv6Range.prefix, 64)
        self.assertEqual(ipv6Range.region.id, "us-east")
        self.assertEqual(ipv6Range.linodes[0], 123)
        self.assertEqual(ipv6Range.is_bgp, False)

        ranges = self.client.networking.ipv6_ranges()

        self.assertEqual(ranges[0].range, "2600:3c01::")
        self.assertEqual(ranges[0].prefix, 64)
        self.assertEqual(ranges[0].region.id, "us-east")
        self.assertEqual(
            ranges[0].route_target, "2600:3c01::ffff:ffff:ffff:ffff"
        )

    def test_get_rules(self):
        """
        Tests that you can submit a correct firewall rules view api request.
        """

        firewall = Firewall(self.client, 123)

        with self.mock_get("/networking/firewalls/123/rules") as m:
            result = firewall.get_rules()
            self.assertEqual(m.call_url, "/networking/firewalls/123/rules")
            self.assertEqual(result["inbound"], [])
            self.assertEqual(result["outbound"], [])
            self.assertEqual(result["inbound_policy"], "DROP")
            self.assertEqual(result["outbound_policy"], "DROP")

    def test_get_rule_versions(self):
        """
        Tests that you can submit a correct firewall rule versions view api request.
        """

        firewall = Firewall(self.client, 123)

        with self.mock_get("/networking/firewalls/123/history") as m:
            result = firewall.rule_versions
            self.assertEqual(m.call_url, "/networking/firewalls/123/history")
            self.assertEqual(result["data"][0]["status"], "enabled")
            self.assertEqual(result["data"][0]["rules"]["version"], 1)
            self.assertEqual(result["data"][0]["status"], "enabled")
            self.assertEqual(result["data"][1]["rules"]["version"], 2)

    def test_get_rule_version(self):
        """
        Tests that you can submit a correct firewall rule version view api request.
        """

        firewall = Firewall(self.client, 123)

        with self.mock_get("/networking/firewalls/123/history/rules/2") as m:
            result = firewall.get_rule_version(2)
            self.assertEqual(
                m.call_url, "/networking/firewalls/123/history/rules/2"
            )
            self.assertEqual(result["inbound"][0]["action"], "ACCEPT")
            self.assertEqual(
                result["inbound"][0]["addresses"]["ipv4"][0], "0.0.0.0/0"
            )
            self.assertEqual(
                result["inbound"][0]["addresses"]["ipv6"][0], "ff00::/8"
            )
            self.assertEqual(
                result["inbound"][0]["description"],
                "A really cool firewall rule.",
            )
            self.assertEqual(
                result["inbound"][0]["label"], "really-cool-firewall-rule"
            )
            self.assertEqual(result["inbound"][0]["ports"], "80")
            self.assertEqual(result["inbound"][0]["protocol"], "TCP")
            self.assertEqual(result["outbound"], [])
            self.assertEqual(result["inbound_policy"], "ACCEPT")
            self.assertEqual(result["outbound_policy"], "DROP")
            self.assertEqual(result["version"], 2)

    def test_rdns_reset(self):
        """
        Tests that the RDNS of an IP and be reset using an explicit null value.
        """

        ip = IPAddress(self.client, "127.0.0.1")

        with self.mock_put("/networking/ips/127.0.0.1") as m:
            ip.rdns = ExplicitNullValue()
            ip.save()

            self.assertEqual(m.call_url, "/networking/ips/127.0.0.1")

            # We need to assert of call_data_raw because
            # call_data drops keys with null values
            self.assertEqual(m.call_data_raw, '{"rdns": null}')

        # Ensure that everything works as expected with a class reference
        with self.mock_put("/networking/ips/127.0.0.1") as m:
            ip.rdns = ExplicitNullValue
            ip.save()

            self.assertEqual(m.call_url, "/networking/ips/127.0.0.1")

            self.assertEqual(m.call_data_raw, '{"rdns": null}')

    def test_get_ip(self):
        """
        Tests retrieving comprehensive IP address information, including all relevant properties.
        """

        ip = IPAddress(self.client, "127.0.0.1")

        def __validate_ip(_ip: IPAddress):
            assert _ip.address == "127.0.0.1"
            assert _ip.gateway == "127.0.0.1"
            assert _ip.linode_id == 123
            assert _ip.interface_id == 456
            assert _ip.prefix == 24
            assert _ip.public
            assert _ip.rdns == "test.example.org"
            assert _ip.region.id == "us-east"
            assert _ip.subnet_mask == "255.255.255.0"
            assert _ip.type == "ipv4"
            assert _ip.vpc_nat_1_1.vpc_id == 242
            assert _ip.vpc_nat_1_1.subnet_id == 194
            assert _ip.vpc_nat_1_1.address == "139.144.244.36"

        __validate_ip(ip)
        ip.invalidate()
        __validate_ip(ip)

    def test_delete_ip(self):
        """
        Tests that deleting an IP creates the correct api request
        """
        with self.mock_delete() as m:
            ip = IPAddress(self.client, "127.0.0.1")
            ip.to(Instance(self.client, 123))
            ip.delete()

            self.assertEqual(m.call_url, "/linode/instances/123/ips/127.0.0.1")

    def test_delete_vlan(self):
        """
        Tests that deleting a VLAN creates the correct api request
        """
        with self.mock_delete() as m:
            self.client.networking.delete_vlan(
                VLAN(self.client, "vlan-test"),
                Region(self.client, "us-southeast"),
            )

            self.assertEqual(
                m.call_url, "/networking/vlans/us-southeast/vlan-test"
            )

    def test_ip_address_reserved_and_tags(self):
        """
        Tests that IPAddress exposes the reserved and tags fields.
        """
        with self.mock_get(
            {
                "address": "127.0.0.1",
                "gateway": "127.0.0.1",
                "linode_id": 123,
                "interface_id": 456,
                "prefix": 24,
                "public": True,
                "rdns": "test.example.org",
                "region": "us-east",
                "subnet_mask": "255.255.255.0",
                "type": "ipv4",
                "vpc_nat_1_1": None,
                "reserved": True,
                "tags": ["lb"],
            }
        ):
            ip = IPAddress(self.client, "127.0.0.1")
            assert ip.reserved is True
            assert ip.tags == ["lb"]

    def test_reserved_ip_address_save_tags(self):
        """
        Tests that saving a ReservedIPAddress sends tags in the PUT body.
        """
        reserved_ip = ReservedIPAddress(
            self.client,
            "66.175.209.100",
            {
                "address": "66.175.209.100",
                "gateway": "66.175.209.1",
                "linode_id": None,
                "prefix": 24,
                "public": True,
                "rdns": "66-175-209-100.ip.linodeusercontent.com",
                "region": "us-east",
                "reserved": True,
                "subnet_mask": "255.255.255.0",
                "tags": ["lb"],
                "type": "ipv4",
            },
        )

        with MethodMock(
            "put",
            {
                "address": "66.175.209.100",
                "gateway": "66.175.209.1",
                "linode_id": None,
                "prefix": 24,
                "public": True,
                "rdns": "66-175-209-100.ip.linodeusercontent.com",
                "region": "us-east",
                "reserved": True,
                "subnet_mask": "255.255.255.0",
                "tags": ["lb", "team:infra"],
                "type": "ipv4",
                "assigned_entity": None,
            },
        ) as m:
            reserved_ip.tags = ["lb", "team:infra"]
            reserved_ip.save()

            assert m.call_url == "/networking/reserved/ips/66.175.209.100"
            body = m.call_data
            assert body["tags"] == ["lb", "team:infra"]
            assert reserved_ip.assigned_entity is None

    def test_reserved_ip_address_delete(self):
        """
        Tests that deleting a ReservedIPAddress calls the correct endpoint.
        """
        with self.mock_delete() as m:
            reserved_ip = ReservedIPAddress(self.client, "66.175.209.100")
            reserved_ip.delete()

            self.assertEqual(
                m.call_url, "/networking/reserved/ips/66.175.209.100"
            )

    def test_ip_address_assigned_entity(self):
        """
        Tests that IPAddress deserializes the assigned_entity field.
        """
        with self.mock_get(
            {
                "address": "66.175.209.100",
                "gateway": "66.175.209.1",
                "linode_id": 123,
                "interface_id": None,
                "prefix": 24,
                "public": True,
                "rdns": "",
                "region": "us-east",
                "subnet_mask": "255.255.255.0",
                "type": "ipv4",
                "vpc_nat_1_1": None,
                "reserved": True,
                "tags": ["lb"],
                "assigned_entity": {
                    "id": 123,
                    "label": "my-linode",
                    "type": "linode",
                    "url": "/v4/linode/instances/123",
                },
            }
        ):
            ip = IPAddress(self.client, "66.175.209.100")
            assert ip.assigned_entity is not None
            assert isinstance(ip.assigned_entity, ReservedIPAssignedEntity)
            assert ip.assigned_entity.id == 123
            assert ip.assigned_entity.label == "my-linode"
            assert ip.assigned_entity.type == "linode"
            assert ip.assigned_entity.url == "/v4/linode/instances/123"

    def test_ip_address_assigned_entity_null(self):
        """
        Tests that IPAddress handles a null assigned_entity field.
        """
        with self.mock_get(
            {
                "address": "66.175.209.101",
                "gateway": "66.175.209.1",
                "linode_id": None,
                "interface_id": None,
                "prefix": 24,
                "public": True,
                "rdns": "",
                "region": "us-east",
                "subnet_mask": "255.255.255.0",
                "type": "ipv4",
                "vpc_nat_1_1": None,
                "reserved": True,
                "tags": [],
                "assigned_entity": None,
            }
        ):
            ip = IPAddress(self.client, "66.175.209.101")
            assert ip.assigned_entity is None

    def test_ip_address_reserved_mutable(self):
        """
        Tests that IPAddress.reserved can be set and saved (convert ephemeral <-> reserved).
        """
        with self.mock_get(
            {
                "address": "66.175.209.100",
                "gateway": "66.175.209.1",
                "linode_id": 123,
                "interface_id": None,
                "prefix": 24,
                "public": True,
                "rdns": "",
                "region": "us-east",
                "subnet_mask": "255.255.255.0",
                "type": "ipv4",
                "vpc_nat_1_1": None,
                "reserved": False,
                "tags": [],
                "assigned_entity": None,
            }
        ):
            ip = IPAddress(self.client, "66.175.209.100")
            assert ip.reserved is False

        with MethodMock(
            "put",
            {
                "address": "66.175.209.100",
                "gateway": "66.175.209.1",
                "linode_id": 123,
                "prefix": 24,
                "public": True,
                "rdns": "",
                "region": "us-east",
                "subnet_mask": "255.255.255.0",
                "type": "ipv4",
                "reserved": True,
                "tags": [],
            },
        ) as m:
            ip.reserved = True
            ip.save()

            assert m.call_url == "/networking/ips/66.175.209.100"
            assert m.call_data["reserved"] is True

    def test_reserved_ip_address_assigned_entity(self):
        """
        Tests that ReservedIPAddress deserializes the assigned_entity field.
        """
        reserved_ip = ReservedIPAddress(
            self.client,
            "66.175.209.100",
            {
                "address": "66.175.209.100",
                "gateway": "66.175.209.1",
                "linode_id": 5678,
                "prefix": 24,
                "public": True,
                "rdns": "",
                "region": "us-east",
                "reserved": True,
                "subnet_mask": "255.255.255.0",
                "tags": ["lb"],
                "type": "ipv4",
                "assigned_entity": {
                    "id": 5678,
                    "label": "my-nodebalancer",
                    "type": "nodebalancer",
                    "url": "/v4/nodebalancers/5678",
                },
            },
        )
        assert reserved_ip.assigned_entity is not None
        assert isinstance(reserved_ip.assigned_entity, ReservedIPAssignedEntity)
        assert reserved_ip.assigned_entity.id == 5678
        assert reserved_ip.assigned_entity.label == "my-nodebalancer"
        assert reserved_ip.assigned_entity.type == "nodebalancer"
        assert reserved_ip.assigned_entity.url == "/v4/nodebalancers/5678"

    def test_instance_ip_allocate_with_address(self):
        """
        Tests that Instance.ip_allocate sends the address field when provided.
        """
        with MethodMock(
            "post",
            {
                "address": "66.175.209.100",
                "gateway": "66.175.209.1",
                "linode_id": 123,
                "prefix": 24,
                "public": True,
                "rdns": "",
                "region": "us-east",
                "subnet_mask": "255.255.255.0",
                "type": "ipv4",
                "reserved": True,
                "tags": [],
            },
        ) as m:
            instance = Instance(self.client, 123)
            ip = instance.ip_allocate(public=True, address="66.175.209.100")

            assert m.call_url == "/linode/instances/123/ips"
            assert m.call_data["address"] == "66.175.209.100"
            assert m.call_data["type"] == "ipv4"
            assert m.call_data["public"] is True
            assert ip.address == "66.175.209.100"

    def test_instance_ip_allocate_without_address(self):
        """
        Tests that Instance.ip_allocate omits address when not provided.
        """
        with MethodMock(
            "post",
            {
                "address": "198.51.100.5",
                "gateway": "198.51.100.1",
                "linode_id": 123,
                "prefix": 24,
                "public": True,
                "rdns": "",
                "region": "us-east",
                "subnet_mask": "255.255.255.0",
                "type": "ipv4",
                "reserved": False,
                "tags": [],
            },
        ) as m:
            instance = Instance(self.client, 123)
            instance.ip_allocate(public=True)

            assert m.call_url == "/linode/instances/123/ips"
            assert "address" not in m.call_data

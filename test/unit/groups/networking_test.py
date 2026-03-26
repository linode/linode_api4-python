from test.unit.base import ClientBaseCase, MethodMock
from test.unit.objects.firewall_test import FirewallTemplatesTest

from linode_api4.objects.networking import ReservedIPAddress


class NetworkingGroupTest(ClientBaseCase):
    """
    Tests methods under the NetworkingGroup class.
    """

    def test_get_templates(self):
        templates = self.client.networking.firewall_templates()

        assert templates[0].slug == "public"
        FirewallTemplatesTest.assert_rules(templates[0].rules)

        assert templates[1].slug == "vpc"
        FirewallTemplatesTest.assert_rules(templates[1].rules)

    def test_reserved_ips_list(self):
        """
        Tests that reserved IPs are listed correctly.
        """
        reserved = self.client.networking.reserved_ips()

        assert len(reserved) == 2
        assert reserved[0].address == "66.175.209.100"
        assert reserved[0].region.id == "us-east"
        assert reserved[0].reserved is True
        assert reserved[0].tags == ["lb"]
        assert reserved[1].address == "66.175.209.101"
        assert reserved[1].tags == []

    def test_reserved_ip_create(self):
        """
        Tests that reserved_ip_create sends the correct request body and returns a
        ReservedIPAddress.
        """
        with MethodMock(
            "post",
            {
                "address": "66.175.209.200",
                "gateway": "66.175.209.1",
                "linode_id": None,
                "prefix": 24,
                "public": True,
                "rdns": "66-175-209-200.ip.linodeusercontent.com",
                "region": "us-east",
                "reserved": True,
                "subnet_mask": "255.255.255.0",
                "tags": ["lb"],
                "type": "ipv4",
                "assigned_entity": None,
            },
        ) as m:
            result = self.client.networking.reserved_ip_create(
                "us-east", tags=["lb"]
            )

            assert m.call_url == "/networking/reserved/ips"
            body = m.call_data
            assert body["region"] == "us-east"
            assert body["tags"] == ["lb"]

            assert isinstance(result, ReservedIPAddress)
            assert result.address == "66.175.209.200"
            assert result.reserved is True
            assert result.tags == ["lb"]
            assert result.assigned_entity is None

    def test_reserved_ip_create_no_tags(self):
        """
        Tests that reserved_ip_create omits tags from the request when not provided.
        """
        with MethodMock(
            "post",
            {
                "address": "66.175.209.201",
                "gateway": "66.175.209.1",
                "linode_id": None,
                "prefix": 24,
                "public": True,
                "rdns": "66-175-209-201.ip.linodeusercontent.com",
                "region": "us-east",
                "reserved": True,
                "subnet_mask": "255.255.255.0",
                "tags": [],
                "type": "ipv4",
            },
        ) as m:
            self.client.networking.reserved_ip_create("us-east")

            body = m.call_data
            assert "tags" not in body

    def test_reserved_ip_types(self):
        """
        Tests that reserved IP types are listed with pricing data.
        """
        types = self.client.networking.reserved_ip_types()

        assert len(types) == 1
        assert types[0].id == "ipv4"
        assert types[0].label == "IPv4 Address"
        assert types[0].price.hourly == 0.005
        assert types[0].price.monthly == 2.0
        assert len(types[0].region_prices) == 2
        assert types[0].region_prices[0].id == "us-east"

    def test_ip_allocate_reserved_with_region(self):
        """
        Tests that ip_allocate with reserved=True and a region creates an unassigned reserved IP.
        """
        with MethodMock(
            "post",
            {
                "address": "66.175.209.200",
                "gateway": "66.175.209.1",
                "linode_id": None,
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
            ip = self.client.networking.ip_allocate(
                reserved=True, region="us-east"
            )

            assert m.call_url == "/networking/ips/"
            body = m.call_data
            assert body["type"] == "ipv4"
            assert body["public"] is True
            assert body["reserved"] is True
            assert body["region"] == "us-east"
            assert "linode_id" not in body
            assert ip.address == "66.175.209.200"
            assert ip.reserved is True

    def test_ip_allocate_reserved_with_linode(self):
        """
        Tests that ip_allocate with reserved=True and a linode assigns a reserved IP to that Instance.
        """
        with MethodMock(
            "post",
            {
                "address": "66.175.209.201",
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
            ip = self.client.networking.ip_allocate(linode=123, reserved=True)

            body = m.call_data
            assert body["linode_id"] == 123
            assert body["reserved"] is True
            assert "region" not in body
            assert ip.linode_id == 123
            assert ip.reserved is True

    def test_ip_allocate_ephemeral(self):
        """
        Tests that ip_allocate without reserved= sends the classic ephemeral request.
        """
        with MethodMock(
            "post",
            {
                "address": "198.51.100.1",
                "gateway": "198.51.100.254",
                "linode_id": 456,
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
            ip = self.client.networking.ip_allocate(linode=456)

            body = m.call_data
            assert body["linode_id"] == 456
            assert body["type"] == "ipv4"
            assert "reserved" not in body
            assert ip.linode_id == 456
            assert ip.reserved is False

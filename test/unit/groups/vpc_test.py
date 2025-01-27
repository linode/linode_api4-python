import datetime
from test.unit.base import ClientBaseCase

from linode_api4 import DATE_FORMAT, VPC, VPCSubnet


class VPCTest(ClientBaseCase):
    """
    Tests methods of the VPC Group
    """

    def test_create_vpc(self):
        """
        Tests that you can create a VPC.
        """

        with self.mock_post("/vpcs/123456") as m:
            vpc = self.client.vpcs.create("test-vpc", "us-southeast")

            self.assertEqual(m.call_url, "/vpcs")

            self.assertEqual(
                m.call_data,
                {
                    "label": "test-vpc",
                    "region": "us-southeast",
                },
            )

            self.assertEqual(vpc._populated, True)
            self.validate_vpc_123456(vpc)

    def test_create_vpc_with_subnet(self):
        """
        Tests that you can create a VPC.
        """

        with self.mock_post("/vpcs/123456") as m:
            vpc = self.client.vpcs.create(
                "test-vpc",
                "us-southeast",
                subnets=[{"label": "test-subnet", "ipv4": "10.0.0.0/24"}],
            )

            self.assertEqual(m.call_url, "/vpcs")

            self.assertEqual(
                m.call_data,
                {
                    "label": "test-vpc",
                    "region": "us-southeast",
                    "subnets": [
                        {"label": "test-subnet", "ipv4": "10.0.0.0/24"}
                    ],
                },
            )

            self.assertEqual(vpc._populated, True)
            self.validate_vpc_123456(vpc)

    def test_list_ips(self):
        """
        Validates that all VPC IPs can be listed.
        """

        with self.mock_get("/vpcs/ips") as m:
            result = self.client.vpcs.ips()

        assert m.call_url == "/vpcs/ips"
        assert len(result) == 1

        ip = result[0]
        assert ip.address == "10.0.0.2"
        assert ip.address_range is None
        assert ip.vpc_id == 123
        assert ip.subnet_id == 456
        assert ip.region == "us-mia"
        assert ip.linode_id == 123
        assert ip.config_id == 456
        assert ip.interface_id == 789
        assert ip.active
        assert ip.nat_1_1 == "172.233.179.133"
        assert ip.gateway == "10.0.0.1"
        assert ip.prefix == 24
        assert ip.subnet_mask == "255.255.255.0"

    def validate_vpc_123456(self, vpc: VPC):
        expected_dt = datetime.datetime.strptime(
            "2018-01-01T00:01:01", DATE_FORMAT
        )

        self.assertEqual(vpc.label, "test-vpc")
        self.assertEqual(vpc.description, "A very real VPC.")
        self.assertEqual(vpc.region.id, "us-southeast")
        self.assertEqual(vpc.created, expected_dt)
        self.assertEqual(vpc.updated, expected_dt)

    def validate_vpc_subnet_789(self, subnet: VPCSubnet):
        expected_dt = datetime.datetime.strptime(
            "2018-01-01T00:01:01", DATE_FORMAT
        )

        self.assertEqual(subnet.label, "test-subnet")
        self.assertEqual(subnet.ipv4, "10.0.0.0/24")
        self.assertEqual(subnet.linodes[0].id, 12345)
        self.assertEqual(subnet.created, expected_dt)
        self.assertEqual(subnet.updated, expected_dt)

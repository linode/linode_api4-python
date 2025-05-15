import datetime
from test.unit.base import ClientBaseCase

from linode_api4 import DATE_FORMAT, VPC, VPCSubnet


class VPCTest(ClientBaseCase):
    """
    Tests methods of the VPC Group
    """

    def test_get_vpc(self):
        """
        Tests that a VPC is loaded correctly by ID
        """

        vpc = VPC(self.client, 123456)
        self.assertEqual(vpc._populated, False)

        self.validate_vpc_123456(vpc)
        self.assertEqual(vpc._populated, True)

    def test_list_vpcs(self):
        """
        Tests that you can list VPCs.
        """

        vpcs = self.client.vpcs()

        self.validate_vpc_123456(vpcs[0])
        self.assertEqual(vpcs[0]._populated, True)

    def test_get_subnet(self):
        """
        Tests that you can list VPCs.
        """

        subnet = VPCSubnet(self.client, 789, 123456)

        self.assertEqual(subnet._populated, False)

        self.validate_vpc_subnet_789(subnet)
        self.assertEqual(subnet._populated, True)
        self.assertEqual(subnet.linodes[0].id, 12345)
        self.assertEqual(subnet.linodes[0].interfaces[0].id, 678)
        self.assertEqual(len(subnet.linodes[0].interfaces), 2)
        self.assertEqual(subnet.linodes[0].interfaces[1].active, False)

    def test_list_subnets(self):
        """
        Tests that you can list VPCs.
        """

        subnets = self.client.vpcs()[0].subnets

        self.validate_vpc_subnet_789(subnets[0])

    def test_create_subnet(self):
        """
        Tests that you can create a subnet.
        """

        with self.mock_post("/vpcs/123456/subnets/789") as m:
            vpc = VPC(self.client, 123456)
            subnet = vpc.subnet_create("test-subnet", "10.0.0.0/24")

            self.assertEqual(m.call_url, "/vpcs/123456/subnets")

            self.assertEqual(
                m.call_data,
                {
                    "label": "test-subnet",
                    "ipv4": "10.0.0.0/24",
                },
            )

            self.validate_vpc_subnet_789(subnet)

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

    def test_list_vpc_ips(self):
        """
        Test that the ips under a specific VPC can be listed.
        """
        vpc = VPC(self.client, 123456)
        vpc_ips = vpc.ips

        self.assertGreater(len(vpc_ips), 0)

        vpc_ip = vpc_ips[0]

        self.assertEqual(vpc_ip.vpc_id, vpc.id)
        self.assertEqual(vpc_ip.address, "10.0.0.2")
        self.assertEqual(vpc_ip.address_range, None)
        self.assertEqual(vpc_ip.subnet_id, 654321)
        self.assertEqual(vpc_ip.region, "us-ord")
        self.assertEqual(vpc_ip.linode_id, 111)
        self.assertEqual(vpc_ip.config_id, 222)
        self.assertEqual(vpc_ip.interface_id, 333)
        self.assertEqual(vpc_ip.active, True)
        self.assertEqual(vpc_ip.nat_1_1, None)
        self.assertEqual(vpc_ip.gateway, "10.0.0.1")
        self.assertEqual(vpc_ip.prefix, 8)
        self.assertEqual(vpc_ip.subnet_mask, "255.0.0.0")

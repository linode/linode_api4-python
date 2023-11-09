import datetime
from test.unit.base import ClientBaseCase

from linode_api4 import DATE_FORMAT, VPC, VPCSubnet
from linode_api4.objects import Volume


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

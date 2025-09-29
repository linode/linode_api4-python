from datetime import datetime
from test.unit.base import ClientBaseCase

from linode_api4 import (
    LinodeInterface,
    LinodeInterfaceDefaultRouteOptions,
    LinodeInterfaceOptions,
    LinodeInterfacePublicIPv4AddressOptions,
    LinodeInterfacePublicIPv4Options,
    LinodeInterfacePublicIPv6Options,
    LinodeInterfacePublicIPv6RangeOptions,
    LinodeInterfacePublicOptions,
    LinodeInterfaceVLANOptions,
    LinodeInterfaceVPCIPv4AddressOptions,
    LinodeInterfaceVPCIPv4Options,
    LinodeInterfaceVPCIPv4RangeOptions,
    LinodeInterfaceVPCOptions,
)


def build_interface_options_public():
    return LinodeInterfaceOptions(
        firewall_id=123,
        default_route=LinodeInterfaceDefaultRouteOptions(
            ipv4=True,
            ipv6=True,
        ),
        public=LinodeInterfacePublicOptions(
            ipv4=LinodeInterfacePublicIPv4Options(
                addresses=[
                    LinodeInterfacePublicIPv4AddressOptions(
                        address="172.30.0.50", primary=True
                    )
                ],
            ),
            ipv6=LinodeInterfacePublicIPv6Options(
                ranges=[
                    LinodeInterfacePublicIPv6RangeOptions(
                        range="2600:3c09:e001:59::/64"
                    )
                ]
            ),
        ),
    )


def build_interface_options_vpc():
    return LinodeInterfaceOptions(
        firewall_id=123,
        default_route=LinodeInterfaceDefaultRouteOptions(
            ipv4=True,
        ),
        vpc=LinodeInterfaceVPCOptions(
            subnet_id=123,
            ipv4=LinodeInterfaceVPCIPv4Options(
                addresses=[
                    LinodeInterfaceVPCIPv4AddressOptions(
                        address="192.168.22.3",
                        primary=True,
                        nat_1_1_address="any",
                    )
                ],
                ranges=[
                    LinodeInterfaceVPCIPv4RangeOptions(range="192.168.22.16/28")
                ],
            ),
        ),
    )


def build_interface_options_vlan():
    return LinodeInterfaceOptions(
        vlan=LinodeInterfaceVLANOptions(
            vlan_label="my_vlan", ipam_address="10.0.0.1/24"
        ),
    )


class LinodeInterfaceTest(ClientBaseCase):
    """
    Tests methods of the LinodeInterface class
    """

    @staticmethod
    def assert_linode_124_interface_123(iface: LinodeInterface):
        assert iface.id == 123

        assert isinstance(iface.created, datetime)
        assert isinstance(iface.updated, datetime)

        assert iface.default_route.ipv4
        assert iface.default_route.ipv6

        assert iface.mac_address == "22:00:AB:CD:EF:01"
        assert iface.version == 1

        assert iface.vlan is None
        assert iface.vpc is None

        # public.ipv4 assertions
        assert iface.public.ipv4.addresses[0].address == "172.30.0.50"
        assert iface.public.ipv4.addresses[0].primary

        assert iface.public.ipv4.shared[0].address == "172.30.0.51"
        assert iface.public.ipv4.shared[0].linode_id == 125

        # public.ipv6 assertions
        assert iface.public.ipv6.ranges[0].range == "2600:3c09:e001:59::/64"
        assert (
            iface.public.ipv6.ranges[0].route_target
            == "2600:3c09::ff:feab:cdef"
        )

        assert iface.public.ipv6.ranges[1].range == "2600:3c09:e001:5a::/64"
        assert (
            iface.public.ipv6.ranges[1].route_target
            == "2600:3c09::ff:feab:cdef"
        )

        assert iface.public.ipv6.shared[0].range == "2600:3c09:e001:2a::/64"
        assert iface.public.ipv6.shared[0].route_target is None

        assert iface.public.ipv6.slaac[0].address == "2600:3c09::ff:feab:cdef"
        assert iface.public.ipv6.slaac[0].prefix == 64

    @staticmethod
    def assert_linode_124_interface_456(iface: LinodeInterface):
        assert iface.id == 456

        assert isinstance(iface.created, datetime)
        assert isinstance(iface.updated, datetime)

        assert iface.default_route.ipv4
        assert not iface.default_route.ipv6

        assert iface.mac_address == "22:00:AB:CD:EF:01"
        assert iface.version == 1

        assert iface.vlan is None
        assert iface.public is None

        # vpc assertions
        assert iface.vpc.vpc_id == 123456
        assert iface.vpc.subnet_id == 789

        assert iface.vpc.ipv4.addresses[0].address == "192.168.22.3"
        assert iface.vpc.ipv4.addresses[0].primary

        assert iface.vpc.ipv4.ranges[0].range == "192.168.22.16/28"
        assert iface.vpc.ipv4.ranges[1].range == "192.168.22.32/28"

    @staticmethod
    def assert_linode_124_interface_789(iface: LinodeInterface):
        assert iface.id == 789

        assert isinstance(iface.created, datetime)
        assert isinstance(iface.updated, datetime)

        assert iface.default_route.ipv4 is None
        assert iface.default_route.ipv6 is None

        assert iface.mac_address == "22:00:AB:CD:EF:01"
        assert iface.version == 1

        assert iface.public is None
        assert iface.vpc is None

        # vlan assertions
        assert iface.vlan.vlan_label == "my_vlan"
        assert iface.vlan.ipam_address == "10.0.0.1/24"

    def test_get_public(self):
        iface = LinodeInterface(self.client, 123, 124)

        self.assert_linode_124_interface_123(iface)
        iface.invalidate()
        self.assert_linode_124_interface_123(iface)

    def test_get_vpc(self):
        iface = LinodeInterface(self.client, 456, 124)

        self.assert_linode_124_interface_456(iface)
        iface.invalidate()
        self.assert_linode_124_interface_456(iface)

    def test_get_vlan(self):
        iface = LinodeInterface(self.client, 789, 124)

        self.assert_linode_124_interface_789(iface)
        iface.invalidate()
        self.assert_linode_124_interface_789(iface)

    def test_update_public(self):
        iface = LinodeInterface(self.client, 123, 124)

        self.assert_linode_124_interface_123(iface)

        iface.default_route.ipv4 = False
        iface.default_route.ipv6 = False

        iface.public.ipv4.addresses = [
            LinodeInterfacePublicIPv4AddressOptions(
                address="172.30.0.51",
                primary=False,
            )
        ]

        iface.public.ipv6.ranges = [
            LinodeInterfacePublicIPv6RangeOptions(
                range="2600:3c09:e001:58::/64"
            )
        ]

        with self.mock_put("/linode/instances/124/interfaces/123") as m:
            iface.save()

            assert m.called

            assert m.call_data == {
                "default_route": {
                    "ipv4": False,
                    "ipv6": False,
                },
                "public": {
                    "ipv4": {
                        "addresses": [
                            {
                                "address": "172.30.0.51",
                                "primary": False,
                            },
                        ]
                    },
                    "ipv6": {
                        "ranges": [
                            {
                                "range": "2600:3c09:e001:58::/64",
                            }
                        ]
                    },
                },
            }

    def test_update_vpc(self):
        iface = LinodeInterface(self.client, 456, 124)

        self.assert_linode_124_interface_456(iface)

        iface.default_route.ipv4 = False

        iface.vpc.subnet_id = 456

        iface.vpc.ipv4.addresses = [
            LinodeInterfaceVPCIPv4AddressOptions(
                address="192.168.22.4", primary=False, nat_1_1_address="auto"
            )
        ]

        iface.vpc.ipv4.ranges = [
            LinodeInterfaceVPCIPv4RangeOptions(
                range="192.168.22.17/28",
            )
        ]

        with self.mock_put("/linode/instances/124/interfaces/456") as m:
            iface.save()

            assert m.called

            assert m.call_data == {
                "default_route": {
                    "ipv4": False,
                },
                "vpc": {
                    "subnet_id": 456,
                    "ipv4": {
                        "addresses": [
                            {
                                "address": "192.168.22.4",
                                "primary": False,
                                "nat_1_1_address": "auto",
                            },
                        ],
                        "ranges": [{"range": "192.168.22.17/28"}],
                    },
                },
            }

    def test_delete(self):
        iface = LinodeInterface(self.client, 123, 124)

        with self.mock_delete() as m:
            iface.delete()
            assert m.called

    def test_firewalls(self):
        iface = LinodeInterface(self.client, 123, 124)

        firewalls = iface.firewalls()

        assert len(firewalls) == 1

        assert firewalls[0].id == 123

        # Check a few fields to make sure the Firewall object was populated
        assert firewalls[0].label == "firewall123"
        assert firewalls[0].rules.inbound[0].action == "ACCEPT"
        assert firewalls[0].status == "enabled"

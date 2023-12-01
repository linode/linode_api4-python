from datetime import datetime
from test.unit.base import ClientBaseCase

from linode_api4 import NetworkInterface
from linode_api4.objects import (
    Config,
    ConfigInterface,
    ConfigInterfaceIPv4,
    Disk,
    Image,
    Instance,
    StackScript,
    Type,
    VPCSubnet,
)


class LinodeTest(ClientBaseCase):
    """
    Tests methods of the Linode class
    """

    def test_get_linode(self):
        """
        Tests that a client is loaded correctly by ID
        """
        linode = Instance(self.client, 123)
        self.assertEqual(linode._populated, False)

        self.assertEqual(linode.label, "linode123")
        self.assertEqual(linode.group, "test")

        self.assertTrue(isinstance(linode.image, Image))
        self.assertEqual(linode.image.label, "Ubuntu 17.04")
        self.assertEqual(
            linode.host_uuid, "3a3ddd59d9a78bb8de041391075df44de62bfec8"
        )
        self.assertEqual(linode.watchdog_enabled, True)

        json = linode._raw_json
        self.assertIsNotNone(json)
        self.assertEqual(json["id"], 123)
        self.assertEqual(json["label"], "linode123")
        self.assertEqual(json["group"], "test")

        # test that the _raw_json stored on the object is sufficient to populate
        # a new object
        linode2 = Instance(self.client, json["id"], json=json)

        self.assertTrue(linode2._populated)
        self.assertEqual(linode2.id, linode.id)
        self.assertEqual(linode2.label, linode.label)
        self.assertEqual(linode2.group, linode.group)
        self.assertEqual(linode2._raw_json, linode._raw_json)

    def test_transfer(self):
        """
        Tests that you can get transfer
        """
        linode = Instance(self.client, 123)

        transfer = linode.transfer

        self.assertEqual(transfer.quota, 471)
        self.assertEqual(transfer.billable, 0)
        self.assertEqual(transfer.used, 10369075)

    def test_rebuild(self):
        """
        Tests that you can rebuild with an image
        """
        linode = Instance(self.client, 123)

        with self.mock_post("/linode/instances/123") as m:
            pw = linode.rebuild("linode/debian9")

            self.assertIsNotNone(pw)
            self.assertTrue(isinstance(pw, str))

            self.assertEqual(m.call_url, "/linode/instances/123/rebuild")

            self.assertEqual(
                m.call_data,
                {
                    "image": "linode/debian9",
                    "root_pass": pw,
                },
            )

    def test_available_backups(self):
        """
        Tests that a Linode can retrieve its own backups
        """
        linode = Instance(self.client, 123)

        backups = linode.available_backups

        # assert we got the correct number of automatic backups
        self.assertEqual(len(backups.automatic), 3)

        # examine one automatic backup
        b = backups.automatic[0]
        self.assertEqual(b.id, 12345)
        self.assertEqual(b._populated, True)
        self.assertEqual(b.status, "successful")
        self.assertEqual(b.type, "auto")
        self.assertEqual(
            b.created,
            datetime(year=2018, month=1, day=9, hour=0, minute=1, second=1),
        )
        self.assertEqual(
            b.updated,
            datetime(year=2018, month=1, day=9, hour=0, minute=1, second=1),
        )
        self.assertEqual(
            b.finished,
            datetime(year=2018, month=1, day=9, hour=0, minute=1, second=1),
        )
        self.assertEqual(b.region.id, "us-east-1a")
        self.assertEqual(b.label, None)
        self.assertEqual(b.message, None)
        self.assertEqual(b.available, True)

        self.assertEqual(len(b.disks), 2)
        self.assertEqual(b.disks[0].size, 1024)
        self.assertEqual(b.disks[0].label, "Debian 8.1 Disk")
        self.assertEqual(b.disks[0].filesystem, "ext4")
        self.assertEqual(b.disks[1].size, 0)
        self.assertEqual(b.disks[1].label, "256MB Swap Image")
        self.assertEqual(b.disks[1].filesystem, "swap")

        self.assertEqual(len(b.configs), 1)
        self.assertEqual(b.configs[0], "My Debian 8.1 Profile")

        # assert that snapshots came back as expected
        self.assertEqual(backups.snapshot.current, None)
        self.assertEqual(backups.snapshot.in_progress, None)

    def test_update_linode(self):
        """
        Tests that a Linode can be updated
        """
        with self.mock_put("linode/instances/123") as m:
            linode = self.client.load(Instance, 123)

            linode.label = "NewLinodeLabel"
            linode.group = "new_group"
            linode.save()

            self.assertEqual(m.call_url, "/linode/instances/123")
            self.assertEqual(
                m.call_data,
                {
                    "alerts": {
                        "cpu": 90,
                        "io": 5000,
                        "network_in": 5,
                        "network_out": 5,
                        "transfer_quota": 80,
                    },
                    "backups": {
                        "enabled": True,
                        "schedule": {"day": "Scheduling", "window": "W02"},
                    },
                    "label": "NewLinodeLabel",
                    "group": "new_group",
                    "tags": ["something"],
                    "watchdog_enabled": True,
                },
            )

    def test_delete_linode(self):
        """
        Tests that deleting a Linode creates the correct api request
        """
        with self.mock_delete() as m:
            linode = Instance(self.client, 123)
            linode.delete()

            self.assertEqual(m.call_url, "/linode/instances/123")

    def test_reboot(self):
        """
        Tests that you can submit a correct reboot api request
        """
        linode = Instance(self.client, 123)
        result = {}

        with self.mock_post(result) as m:
            linode.reboot()
            self.assertEqual(m.call_url, "/linode/instances/123/reboot")

    def test_shutdown(self):
        """
        Tests that you can submit a correct shutdown api request
        """
        linode = Instance(self.client, 123)
        result = {}

        with self.mock_post(result) as m:
            linode.shutdown()
            self.assertEqual(m.call_url, "/linode/instances/123/shutdown")

    def test_boot(self):
        """
        Tests that you can submit a correct boot api request
        """
        linode = Instance(self.client, 123)
        result = {}

        with self.mock_post(result) as m:
            linode.boot()
            self.assertEqual(m.call_url, "/linode/instances/123/boot")

    def test_resize(self):
        """
        Tests that you can submit a correct resize api request
        """
        linode = Instance(self.client, 123)
        result = {}

        with self.mock_post(result) as m:
            linode.resize(new_type="g6-standard-1")
            self.assertEqual(m.call_url, "/linode/instances/123/resize")
            self.assertEqual(m.call_data["type"], "g6-standard-1")

    def test_resize_with_class(self):
        """
        Tests that you can submit a correct resize api request with a Base class type
        """
        linode = Instance(self.client, 123)
        ltype = Type(self.client, "g6-standard-2")
        result = {}

        with self.mock_post(result) as m:
            linode.resize(new_type=ltype)
            self.assertEqual(m.call_url, "/linode/instances/123/resize")
            self.assertEqual(m.call_data["type"], "g6-standard-2")

    def test_boot_with_config(self):
        """
        Tests that you can submit a correct boot with a config api request
        """
        linode = Instance(self.client, 123)
        config = linode.configs[0]
        result = {}

        with self.mock_post(result) as m:
            linode.boot(config=config)
            self.assertEqual(m.call_url, "/linode/instances/123/boot")

    def test_mutate(self):
        """
        Tests that you can submit a correct mutate api request
        """
        linode = Instance(self.client, 123)
        result = {}

        with self.mock_post(result) as m:
            linode.mutate()
            self.assertEqual(m.call_url, "/linode/instances/123/mutate")
            self.assertEqual(m.call_data["allow_auto_disk_resize"], True)

    def test_firewalls(self):
        """
        Tests that you can submit a correct firewalls api request
        """
        linode = Instance(self.client, 123)

        with self.mock_get("/linode/instances/123/firewalls") as m:
            result = linode.firewalls()
            self.assertEqual(m.call_url, "/linode/instances/123/firewalls")
            self.assertEqual(len(result), 1)

    def test_volumes(self):
        """
        Tests that you can submit a correct volumes api request
        """
        linode = Instance(self.client, 123)

        with self.mock_get("/linode/instances/123/volumes") as m:
            result = linode.volumes()
            self.assertEqual(m.call_url, "/linode/instances/123/volumes")
            self.assertEqual(len(result), 1)

    def test_nodebalancers(self):
        """
        Tests that you can submit a correct nodebalancers api request
        """
        linode = Instance(self.client, 123)

        with self.mock_get("/linode/instances/123/nodebalancers") as m:
            result = linode.nodebalancers()
            self.assertEqual(m.call_url, "/linode/instances/123/nodebalancers")
            self.assertEqual(len(result), 1)

    def test_transfer_year_month(self):
        """
        Tests that you can submit a correct transfer api request
        """
        linode = Instance(self.client, 123)

        with self.mock_get("/linode/instances/123/transfer/2023/4") as m:
            linode.transfer_year_month(2023, 4)
            self.assertEqual(
                m.call_url, "/linode/instances/123/transfer/2023/4"
            )

    def test_duplicate(self):
        """
        Tests that you can submit a correct disk clone api request
        """
        disk = Disk(self.client, 12345, 123)

        with self.mock_post("/linode/instances/123/disks/12345/clone") as m:
            disk.duplicate()
            self.assertEqual(
                m.call_url, "/linode/instances/123/disks/12345/clone"
            )

    def test_disk_password(self):
        """
        Tests that you can submit a correct disk password reset api request
        """
        disk = Disk(self.client, 12345, 123)

        with self.mock_post({}) as m:
            disk.reset_root_password()
            self.assertEqual(
                m.call_url, "/linode/instances/123/disks/12345/password"
            )

    def test_instance_password(self):
        """
        Tests that you can submit a correct instance password reset api request
        """
        instance = Instance(self.client, 123)

        with self.mock_post({}) as m:
            instance.reset_instance_root_password()
            self.assertEqual(m.call_url, "/linode/instances/123/password")

    def test_ips(self):
        """
        Tests that you can submit a correct ips api request
        """
        linode = Instance(self.client, 123)

        ips = linode.ips

        self.assertIsNotNone(ips.ipv4)
        self.assertIsNotNone(ips.ipv6)
        self.assertIsNotNone(ips.ipv4.public)
        self.assertIsNotNone(ips.ipv4.private)
        self.assertIsNotNone(ips.ipv4.shared)
        self.assertIsNotNone(ips.ipv4.reserved)
        self.assertIsNotNone(ips.ipv6.slaac)
        self.assertIsNotNone(ips.ipv6.link_local)
        self.assertIsNotNone(ips.ipv6.ranges)

    def test_initiate_migration(self):
        """
        Tests that you can initiate a pending migration
        """
        linode = Instance(self.client, 123)
        result = {}

        with self.mock_post(result) as m:
            linode.initiate_migration()
            self.assertEqual(m.call_url, "/linode/instances/123/migrate")

    def test_create_disk(self):
        """
        Tests that disk_create behaves as expected
        """
        linode = Instance(self.client, 123)

        with self.mock_post("/linode/instances/123/disks/12345") as m:
            disk, gen_pass = linode.disk_create(
                1234,
                label="test",
                authorized_users=["test"],
                image="linode/debian10",
            )
            self.assertEqual(m.call_url, "/linode/instances/123/disks")
            print(m.call_data)
            self.assertEqual(
                m.call_data,
                {
                    "size": 1234,
                    "label": "test",
                    "root_pass": gen_pass,
                    "image": "linode/debian10",
                    "authorized_users": ["test"],
                    "read_only": False,
                },
            )

        assert disk.id == 12345

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


class DiskTest(ClientBaseCase):
    """
    Tests for the Disk object
    """

    def test_resize(self):
        """
        Tests that a resize is submitted correctly
        """
        disk = Disk(self.client, 12345, 123)

        with self.mock_post({}) as m:
            r = disk.resize(1000)

            self.assertTrue(r)

            self.assertEqual(
                m.call_url, "/linode/instances/123/disks/12345/resize"
            )
            self.assertEqual(m.call_data, {"size": 1000})


class ConfigTest(ClientBaseCase):
    """
    Tests for the Config object
    """

    def test_update_interfaces(self):
        """
        Tests that a configs interfaces update correctly
        """

        json = self.client.get("/linode/instances/123/configs/456789")
        config = Config(self.client, 456789, 123, json=json)

        with self.mock_put("/linode/instances/123/configs/456789") as m:
            new_interfaces = [
                {"purpose": "public", "primary": True},
                ConfigInterface("vlan", label="cool-vlan"),
            ]
            expected_body = [new_interfaces[0], new_interfaces[1]._serialize()]

            config.interfaces = new_interfaces

            config.save()

            self.assertEqual(m.call_url, "/linode/instances/123/configs/456789")
            self.assertEqual(m.call_data.get("interfaces"), expected_body)

    def test_get_config(self):
        json = self.client.get("/linode/instances/123/configs/456789")
        config = Config(self.client, 456789, 123, json=json)

        self.assertEqual(config.root_device, "/dev/sda")
        self.assertEqual(config.comments, "")
        self.assertIsNotNone(config.helpers)
        self.assertEqual(config.label, "My Ubuntu 17.04 LTS Profile")
        self.assertEqual(
            config.created,
            datetime(year=2014, month=10, day=7, hour=20, minute=4, second=0),
        )
        self.assertEqual(config.memory_limit, 0)
        self.assertEqual(config.id, 456789)
        self.assertIsNotNone(config.interfaces)
        self.assertEqual(config.run_level, "default")
        self.assertIsNone(config.initrd)
        self.assertEqual(config.virt_mode, "paravirt")
        self.assertIsNotNone(config.devices)

    def test_interface_ipv4(self):
        json = {"vpc": "10.0.0.1", "nat_1_1": "any"}

        ipv4 = ConfigInterfaceIPv4.from_json(json)

        self.assertEqual(ipv4.vpc, "10.0.0.1")
        self.assertEqual(ipv4.nat_1_1, "any")


class StackScriptTest(ClientBaseCase):
    """
    Tests the methods of the StackScript class.
    """

    def test_get_stackscript(self):
        """
        Tests that a stackscript is loaded correctly by ID
        """
        stackscript = StackScript(self.client, 10079)

        self.assertEqual(stackscript.id, 10079)
        self.assertEqual(stackscript.deployments_active, 1)
        self.assertEqual(stackscript.deployments_total, 12)
        self.assertEqual(stackscript.rev_note, "Set up MySQL")
        self.assertTrue(stackscript.mine)
        self.assertTrue(stackscript.is_public)
        self.assertIsNotNone(stackscript.user_defined_fields)
        self.assertIsNotNone(stackscript.images)


class TypeTest(ClientBaseCase):
    def test_get_types(self):
        """
        Tests that Linode types can be returned
        """
        types = self.client.linode.types()

        self.assertEqual(len(types), 4)
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

    def test_get_type_by_id(self):
        """
        Tests that a Linode type is loaded correctly by ID
        """
        t = Type(self.client, "g5-nanode-1")
        self.assertEqual(t._populated, False)

        self.assertEqual(t.vcpus, 1)
        self.assertEqual(t.gpus, 0)
        self.assertEqual(t.label, "Linode 1024")
        self.assertEqual(t.disk, 20480)
        self.assertEqual(t.type_class, "nanode")
        self.assertEqual(t.region_prices[0].id, "us-east")

    def test_get_type_gpu(self):
        """
        Tests that gpu types load up right
        """
        t = Type(self.client, "g5-gpu-2")
        self.assertEqual(t._populated, False)

        self.assertEqual(t.gpus, 1)
        self.assertEqual(t._populated, True)

    def test_save_noforce(self):
        """
        Tests that a client will only save if changes are detected
        """
        linode = Instance(self.client, 123)
        self.assertEqual(linode._populated, False)

        self.assertEqual(linode.label, "linode123")
        self.assertEqual(linode.group, "test")

        assert not linode._changed

        with self.mock_put("linode/instances") as m:
            linode.save(force=False)
            assert not m.called

        linode.label = "blah"
        assert linode._changed

        with self.mock_put("linode/instances") as m:
            linode.save(force=False)
            assert m.called
            assert m.call_url == "/linode/instances/123"
            assert m.call_data["label"] == "blah"

        assert not linode._changed

    def test_save_force(self):
        """
        Tests that a client will forcibly save by default
        """
        linode = Instance(self.client, 123)
        self.assertEqual(linode._populated, False)

        self.assertEqual(linode.label, "linode123")
        self.assertEqual(linode.group, "test")

        assert not linode._changed

        with self.mock_put("linode/instances") as m:
            linode.save()
            assert m.called


class ConfigInterfaceTest(ClientBaseCase):
    def test_list(self):
        config = Config(self.client, 456789, 123)
        config._api_get()
        assert {v.id for v in config.interfaces} == {123, 321, 456}
        assert {v.purpose for v in config.interfaces} == {
            "vlan",
            "vpc",
            "public",
        }

    def test_update(self):
        config = Config(self.client, 456789, 123)
        config._api_get()
        config.interfaces = [
            {"purpose": "public"},
            ConfigInterface(
                purpose="vlan", label="cool-vlan", ipam_address="10.0.0.4/32"
            ),
        ]

        with self.mock_put("linode/instances/123/configs/456789") as m:
            config.save()
            assert m.call_url == "/linode/instances/123/configs/456789"
            assert m.call_data["interfaces"] == [
                {"purpose": "public"},
                {
                    "purpose": "vlan",
                    "label": "cool-vlan",
                    "ipam_address": "10.0.0.4/32",
                },
            ]


class TestNetworkInterface(ClientBaseCase):
    def test_create_interface_public(self):
        config = Config(self.client, 456789, 123)
        config._api_get()

        with self.mock_post(
            "linode/instances/123/configs/456789/interfaces/456"
        ) as m:
            interface = config.interface_create_public(primary=True)

            assert m.called
            assert (
                m.call_url == "/linode/instances/123/configs/456789/interfaces"
            )
            assert m.method == "post"
            assert m.call_data == {"purpose": "public", "primary": True}

            assert interface.id == 456
            assert interface.purpose == "public"
            assert interface.primary

    def test_create_interface_vlan(self):
        config = Config(self.client, 456789, 123)
        config._api_get()

        with self.mock_post(
            "linode/instances/123/configs/456789/interfaces/321"
        ) as m:
            interface = config.interface_create_vlan(
                "test-interface", ipam_address="10.0.0.2/32"
            )

            assert m.called
            assert (
                m.call_url == "/linode/instances/123/configs/456789/interfaces"
            )
            assert m.method == "post"
            assert m.call_data == {
                "purpose": "vlan",
                "label": "test-interface",
                "ipam_address": "10.0.0.2/32",
            }

            assert interface.id == 321
            assert interface.purpose == "vlan"
            assert not interface.primary
            assert interface.label == "test-interface"
            assert interface.ipam_address == "10.0.0.2"

    def test_create_interface_vpc(self):
        config = Config(self.client, 456789, 123)
        config._api_get()

        with self.mock_post(
            "linode/instances/123/configs/456789/interfaces/123"
        ) as m:
            interface = config.interface_create_vpc(
                subnet=VPCSubnet(self.client, 789, 123456),
                primary=True,
                ipv4=ConfigInterfaceIPv4(vpc="10.0.0.4", nat_1_1="any"),
                ip_ranges=["10.0.0.0/24"],
            )

            assert m.called
            assert (
                m.call_url == "/linode/instances/123/configs/456789/interfaces"
            )
            assert m.method == "post"
            assert m.call_data == {
                "purpose": "vpc",
                "primary": True,
                "subnet_id": 789,
                "ipv4": {"vpc": "10.0.0.4", "nat_1_1": "any"},
                "ip_ranges": ["10.0.0.0/24"],
            }

            assert interface.id == 123
            assert interface.purpose == "vpc"
            assert interface.primary
            assert interface.vpc.id == 123456
            assert interface.subnet.id == 789
            assert interface.ipv4.vpc == "10.0.0.2"
            assert interface.ipv4.nat_1_1 == "any"
            assert interface.ip_ranges == ["10.0.0.0/24"]

    def test_update(self):
        interface = NetworkInterface(self.client, 123, 456789, 123)
        interface._api_get()

        interface.ipv4.vpc = "10.0.0.3"
        interface.primary = False
        interface.ip_ranges = ["10.0.0.2/32"]

        with self.mock_put(
            "linode/instances/123/configs/456789/interfaces/123/put"
        ) as m:
            interface.save()

            assert m.called
            assert (
                m.call_url
                == "/linode/instances/123/configs/456789/interfaces/123"
            )
            assert m.method == "put"
            assert m.call_data == {
                "primary": False,
                "ipv4": {"vpc": "10.0.0.3", "nat_1_1": "any"},
                "ip_ranges": ["10.0.0.2/32"],
            }

    def test_get_vlan(self):
        interface = NetworkInterface(self.client, 321, 456789, instance_id=123)
        interface._api_get()

        self.assertEqual(interface.id, 321)
        self.assertEqual(interface.ipam_address, "10.0.0.2")
        self.assertEqual(interface.purpose, "vlan")
        self.assertEqual(interface.label, "test-interface")

    def test_get_vpc(self):
        interface = NetworkInterface(self.client, 123, 456789, instance_id=123)
        interface._api_get()

        self.assertEqual(interface.id, 123)
        self.assertEqual(interface.purpose, "vpc")
        self.assertEqual(interface.vpc.id, 123456)
        self.assertEqual(interface.subnet.id, 789)
        self.assertEqual(interface.ipv4.vpc, "10.0.0.2")
        self.assertEqual(interface.ipv4.nat_1_1, "any")
        self.assertEqual(interface.ip_ranges, ["10.0.0.0/24"])
        self.assertEqual(interface.active, True)

    def test_list(self):
        config = Config(self.client, 456789, 123)
        config._api_get()
        interfaces = config.network_interfaces

        assert {v.id for v in interfaces} == {123, 321, 456}
        assert {v.purpose for v in interfaces} == {
            "vlan",
            "vpc",
            "public",
        }

        for v in interfaces:
            assert isinstance(v, NetworkInterface)

    def test_reorder(self):
        config = Config(self.client, 456789, 123)
        config._api_get()
        interfaces = config.network_interfaces

        with self.mock_post({}) as m:
            interfaces.reverse()
            # Let's make sure it supports both IDs and NetworkInterfaces
            interfaces[2] = interfaces[2].id

            config.interface_reorder(interfaces)

            assert (
                m.call_url
                == "/linode/instances/123/configs/456789/interfaces/order"
            )

            assert m.call_data == {"ids": [321, 123, 456]}

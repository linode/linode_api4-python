from datetime import datetime
from test.base import ClientBaseCase

from linode_api4.objects import Config, Disk, Image, Instance, StackScript, Type


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
                    "label": "NewLinodeLabel",
                    "group": "new_group",
                    "tags": ["something"],
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
            self.assertEquals(len(result), 1)

    def test_volumes(self):
        """
        Tests that you can submit a correct volumes api request
        """
        linode = Instance(self.client, 123)

        with self.mock_get("/linode/instances/123/volumes") as m:
            result = linode.volumes()
            self.assertEqual(m.call_url, "/linode/instances/123/volumes")
            self.assertEquals(len(result), 1)

    def test_nodebalancers(self):
        """
        Tests that you can submit a correct nodebalancers api request
        """
        linode = Instance(self.client, 123)

        with self.mock_get("/linode/instances/123/nodebalancers") as m:
            result = linode.nodebalancers()
            self.assertEqual(m.call_url, "/linode/instances/123/nodebalancers")
            self.assertEquals(len(result), 1)

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
                {"purpose": "public"},
                {"purpose": "vlan", "label": "cool-vlan"},
            ]

            config.interfaces = new_interfaces

            config.save()

            self.assertEqual(m.call_url, "/linode/instances/123/configs/456789")
            self.assertEqual(m.call_data.get("interfaces"), new_interfaces)

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

from datetime import datetime
from test.base import ClientBaseCase

from linode_api4.objects import Config, Disk, Image, Instance, Type
from linode_api4.objects.base import MappedObject


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

        json = linode._raw_json
        self.assertIsNotNone(json)
        self.assertEqual(json['id'], 123)
        self.assertEqual(json['label'], 'linode123')
        self.assertEqual(json['group'], 'test')

        # test that the _raw_json stored on the object is sufficient to populate
        # a new object
        linode2 = Instance(self.client, json['id'], json=json)

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

        with self.mock_post('/linode/instances/123') as m:
            pw = linode.rebuild('linode/debian9')

            self.assertIsNotNone(pw)
            self.assertTrue(isinstance(pw, str))

            self.assertEqual(m.call_url, '/linode/instances/123/rebuild')

            self.assertEqual(m.call_data, {
                "image": "linode/debian9",
                "root_pass": pw,
            })

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
        self.assertEqual(b.status, 'successful')
        self.assertEqual(b.type, 'auto')
        self.assertEqual(b.created, datetime(year=2018, month=1, day=9, hour=0,
                                             minute=1, second=1))
        self.assertEqual(b.updated, datetime(year=2018, month=1, day=9, hour=0,
                                             minute=1, second=1))
        self.assertEqual(b.finished, datetime(year=2018, month=1, day=9, hour=0,
                                             minute=1, second=1))
        self.assertEqual(b.region.id, 'us-east-1a')
        self.assertEqual(b.label, None)
        self.assertEqual(b.message, None)

        self.assertEqual(len(b.disks), 2)
        self.assertEqual(b.disks[0].size, 1024)
        self.assertEqual(b.disks[0].label, 'Debian 8.1 Disk')
        self.assertEqual(b.disks[0].filesystem, 'ext4')
        self.assertEqual(b.disks[1].size, 0)
        self.assertEqual(b.disks[1].label, '256MB Swap Image')
        self.assertEqual(b.disks[1].filesystem, 'swap')

        self.assertEqual(len(b.configs), 1)
        self.assertEqual(b.configs[0], 'My Debian 8.1 Profile')

        # assert that snapshots came back as expected
        self.assertEqual(backups.snapshot.current, None)
        self.assertEqual(backups.snapshot.in_progress, None)

    def test_update_linode(self):
        """
        Tests that a Linode can be updated
        """
        with self.mock_put('linode/instances/123') as m:
            linode = self.client.load(Instance, 123)

            linode.label = "NewLinodeLabel"
            linode.group = "new_group"
            linode.save()

            self.assertEqual(m.call_url, '/linode/instances/123')
            self.assertEqual(m.call_data, {
                "alerts": {
                    "cpu": 90,
                    "io": 5000,
                    "network_in": 5,
                    "network_out": 5,
                    "transfer_quota": 80
                },
                "label": "NewLinodeLabel",
                "group": "new_group",
                "tags": ["something"],
            })

    def test_delete_linode(self):
        """
        Tests that deleting a Linode creates the correct api request
        """
        with self.mock_delete() as m:
            linode = Instance(self.client, 123)
            linode.delete()

            self.assertEqual(m.call_url, '/linode/instances/123')

    def test_reboot(self):
        """
        Tests that you can submit a correct reboot api request
        """
        linode = Instance(self.client, 123)
        result = {}

        with self.mock_post(result) as m:
            linode.reboot()
            self.assertEqual(m.call_url, '/linode/instances/123/reboot')

    def test_shutdown(self):
        """
        Tests that you can submit a correct shutdown api request
        """
        linode = Instance(self.client, 123)
        result = {}

        with self.mock_post(result) as m:
            linode.shutdown()
            self.assertEqual(m.call_url, '/linode/instances/123/shutdown')

    def test_boot(self):
        """
        Tests that you can submit a correct boot api request
        """
        linode = Instance(self.client, 123)
        result = {}

        with self.mock_post(result) as m:
            linode.boot()
            self.assertEqual(m.call_url, '/linode/instances/123/boot')

    def test_resize(self):
        """
        Tests that you can submit a correct resize api request
        """
        linode = Instance(self.client, 123)
        result = {}

        with self.mock_post(result) as m:
            linode.resize(new_type='g6-standard-1')
            self.assertEqual(m.call_url, '/linode/instances/123/resize')
            self.assertEqual(m.call_data, {'type': 'g6-standard-1'})

    def test_resize_with_class(self):
        """
        Tests that you can submit a correct resize api request with a Base class type
        """
        linode = Instance(self.client, 123)
        ltype = Type(self.client, 'g6-standard-2')
        result = {}

        with self.mock_post(result) as m:
            linode.resize(new_type=ltype)
            self.assertEqual(m.call_url, '/linode/instances/123/resize')
            self.assertEqual(m.call_data, {'type': 'g6-standard-2'})

    def test_boot_with_config(self):
        """
        Tests that you can submit a correct boot with a config api request
        """
        linode = Instance(self.client, 123)
        config = linode.configs[0]
        result = {}

        with self.mock_post(result) as m:
            linode.boot(config=config)
            self.assertEqual(m.call_url, '/linode/instances/123/boot')

    def test_mutate(self):
        """
        Tests that you can submit a correct mutate api request
        """
        linode = Instance(self.client, 123)
        result = {}

        with self.mock_post(result) as m:
            linode.mutate()
            self.assertEqual(m.call_url, '/linode/instances/123/mutate')

    def test_initiate_migration(self):
        """
        Tests that you can initiate a pending migration
        """
        linode = Instance(self.client, 123)
        result = {}

        with self.mock_post(result) as m:
            linode.initiate_migration()
            self.assertEqual(m.call_url, '/linode/instances/123/migrate')


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

            self.assertEqual(m.call_url, '/linode/instances/123/disks/12345/resize')
            self.assertEqual(m.call_data, {"size": 1000})


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

    def test_get_type_by_id(self):
        """
        Tests that a Linode type is loaded correctly by ID
        """
        t = Type(self.client, 'g5-nanode-1')
        self.assertEqual(t._populated, False)

        self.assertEqual(t.vcpus, 1)
        self.assertEqual(t.gpus, 0)
        self.assertEqual(t.label, "Linode 1024")
        self.assertEqual(t.disk, 20480)
        self.assertEqual(t.type_class, 'nanode')

    def test_get_type_gpu(self):
        """
        Tests that gpu types load up right
        """
        t = Type(self.client, "g5-gpu-2")
        self.assertEqual(t._populated, False)

        self.assertEqual(t.gpus, 1)
        self.assertEqual(t._populated, True)

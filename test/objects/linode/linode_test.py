from datetime import datetime

from test.base import ClientBaseCase
from linode.objects.base import MappedObject

from linode.objects import Image, Linode


class LinodeTest(ClientBaseCase):
    """
    Tests methods of the Linode class
    """
    def test_get_linode(self):
        """
        Tests that a client is loaded correctly by ID
        """
        linode = Linode(self.client, 123)
        self.assertEqual(linode._populated, False)

        self.assertEqual(linode.label, "linode123")
        self.assertEqual(linode.group, "test")

        self.assertTrue(isinstance(linode.image, Image))
        self.assertEqual(linode.image.label, "Ubuntu 17.04")

    def test_rebuild(self):
        """
        Tests that you can rebuild with an image
        """
        linode = Linode(self.client, 123)

        # barebones result of a rebuild
        result = {
            "config": [],
            "disks": []
        }

        with self.mock_post(result) as m:
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
        linode = Linode(self.client, 123)

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

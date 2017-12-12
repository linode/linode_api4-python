from datetime import datetime

from test.base import ClientBaseCase

from linode.objects import Volume


class VolumeTest(ClientBaseCase):
    """
    Tests methods of the Volume class
    """
    def test_get_volume(self):
        """
        Tests that a volume is loaded correctly by ID
        """
        volume = Volume(self.client, 1)
        self.assertEqual(volume._populated, False)

        self.assertEqual(volume.label, 'block1')
        self.assertEqual(volume._populated, True)

        self.assertEqual(volume.size, 40)
        self.assertEqual(volume.linode, None)
        self.assertEqual(volume.status, 'active')
        self.assertIsInstance(volume.updated, datetime)
        self.assertEqual(volume.region.id, 'us-east-1a')

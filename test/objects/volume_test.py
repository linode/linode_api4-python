from datetime import datetime
from test.base import ClientBaseCase

from linode_api4.objects import Volume


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

        assert volume.tags == ["something"]

    def test_update_volume_tags(self):
        """
        Tests that updating tags on an entity send the correct request
        """
        volume = self.client.volumes().first()

        with self.mock_put('volumes/1') as m:
            volume.tags = ['test1', 'test2']
            volume.save()

            assert m.call_url == '/volumes/{}'.format(volume.id)
            assert m.call_data['tags'] == ['test1', 'test2']

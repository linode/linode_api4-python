from datetime import datetime
from test.unit.base import ClientBaseCase

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

        self.assertEqual(volume.label, "block1")
        self.assertEqual(volume._populated, True)

        self.assertEqual(volume.size, 40)
        self.assertEqual(volume.linode, None)
        self.assertEqual(volume.status, "active")
        self.assertIsInstance(volume.updated, datetime)
        self.assertEqual(volume.region.id, "us-east-1a")

        assert volume.tags == ["something"]

        self.assertEqual(volume.filesystem_path, "this/is/a/file/path")
        self.assertEqual(volume.hardware_type, "hdd")
        self.assertEqual(volume.linode_label, None)

    def test_update_volume_tags(self):
        """
        Tests that updating tags on an entity send the correct request
        """
        volume = self.client.volumes().first()

        with self.mock_put("volumes/1") as m:
            volume.tags = ["test1", "test2"]
            volume.save()

            assert m.call_url == "/volumes/{}".format(volume.id)
            assert m.call_data["tags"] == ["test1", "test2"]

    def test_clone_volume(self):
        """
        Tests that cloning a volume returns new volume object with
        same region and the given label
        """
        volume_to_clone = self.client.volumes().first()

        with self.mock_post(f"volumes/{volume_to_clone.id}") as mock:
            new_volume = volume_to_clone.clone("new-volume")
            assert mock.call_url == f"/volumes/{volume_to_clone.id}/clone"
            self.assertEqual(
                str(new_volume.region),
                str(volume_to_clone.region),
                "the regions should be the same",
            )
            assert new_volume.id != str(volume_to_clone.id)

    def test_resize_volume(self):
        """
        Tests that resizing a given volume volume works
        """
        volume = self.client.volumes().first()

        with self.mock_post(f"volumes/{volume.id}") as mock:
            volume.resize(3048)
            assert mock.call_url == f"/volumes/{volume.id}/resize"
            assert str(mock.call_data["size"]) == "3048"

    def test_detach_volume(self):
        """
        Tests that detaching the volume succeeds
        """
        volume = self.client.volumes()[2]

        with self.mock_post(f"volumes/{volume.id}") as mock:
            result = volume.detach()
            assert mock.call_url == f"/volumes/{volume.id}/detach"
            assert result is True

    def test_attach_volume_to_linode(self):
        """
        Tests that the given volume attaches to the Linode via id
        """
        volume = self.client.volumes().first()

        with self.mock_post(f"volumes/{volume.id}") as mock:
            result = volume.attach(1)
            assert mock.call_url == f"/volumes/{volume.id}/attach"
            assert result is True
            assert str(mock.call_data["linode_id"]) == "1"

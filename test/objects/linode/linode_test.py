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

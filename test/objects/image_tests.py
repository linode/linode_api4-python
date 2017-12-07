from datetime import datetime

from test.base import ClientBaseCase
from linode.objects.base import MappedObject

from linode.objects import Image


class ImageTest(ClientBaseCase):
    """
    Tests methods of the Image class
    """
    def test_get_image(self):
        """
        Tests that an image is loaded correctly by ID
        """
        image = Image(self.client, 'linode/debian9')
        self.assertEqual(image._populated, False)

        self.assertEqual(image.label, 'Debian 9')
        self.assertEqual(image._populated, True)

        self.assertEqual(image.vendor, 'Debian')
        self.assertEqual(image.description, None)
        self.assertEqual(image.deprecated, False)
        self.assertEqual(image.status, "available")
        self.assertEqual(image.type, "manual")
        self.assertEqual(image.creator, "linode")
        self.assertEqual(image.filesystem, "ext4")

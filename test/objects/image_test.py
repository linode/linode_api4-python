from datetime import datetime

from test.base import ClientBaseCase

from linode_api4.objects import Image


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
        self.assertEqual(image.created_by, "linode")
        self.assertEqual(image.size, 1100)

        self.assertEqual(image.eol, datetime(
            year=2026, month=7, day=1, hour=4, minute=0, second=0
        ))

        self.assertEqual(image.expiry, datetime(
            year=2026, month=8, day=1, hour=4, minute=0, second=0
        ))

        self.assertEqual(image.updated, datetime(
            year=2020, month=7, day=1, hour=4, minute=0, second=0
        ))

    def test_image_create_upload(self):
        """
        Test that an image upload URL can be created successfully.
        """

        with self.mock_post("/images/upload") as m:
            image, url = self.client.image_create_upload(
                "Realest Image Upload",
                "us-southeast",
                description="very real image upload.",
            )

            self.assertEqual(m.call_url, "/images/upload")
            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_data,
                {
                    "label": "Realest Image Upload",
                    "region": "us-southeast",
                    "description": "very real image upload."
                }
            )

        self.assertEqual(image.id, "private/1337")
        self.assertEqual(image.label, "Realest Image Upload")
        self.assertEqual(image.description, "very real image upload.")

        self.assertEqual(url, "https://linode.com/")

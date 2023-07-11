from datetime import datetime
from io import BytesIO
from test.unit.base import ClientBaseCase
from typing import BinaryIO
from unittest.mock import patch

from linode_api4.objects import Image

# A minimal gzipped image that will be accepted by the API
TEST_IMAGE_CONTENT = (
    b"\x1F\x8B\x08\x08\xBD\x5C\x91\x60\x00\x03\x74\x65\x73\x74\x2E\x69"
    b"\x6D\x67\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00"
)


class ImageTest(ClientBaseCase):
    """
    Tests methods of the Image class
    """

    def test_get_image(self):
        """
        Tests that an image is loaded correctly by ID
        """
        image = Image(self.client, "linode/debian9")
        self.assertEqual(image._populated, False)

        self.assertEqual(image.label, "Debian 9")
        self.assertEqual(image._populated, True)

        self.assertEqual(image.vendor, "Debian")
        self.assertEqual(image.description, None)
        self.assertEqual(image.deprecated, False)
        self.assertEqual(image.status, "available")
        self.assertEqual(image.type, "manual")
        self.assertEqual(image.created_by, "linode")
        self.assertEqual(image.size, 1100)

        self.assertEqual(
            image.eol,
            datetime(year=2026, month=7, day=1, hour=4, minute=0, second=0),
        )

        self.assertEqual(
            image.expiry,
            datetime(year=2026, month=8, day=1, hour=4, minute=0, second=0),
        )

        self.assertEqual(
            image.updated,
            datetime(year=2020, month=7, day=1, hour=4, minute=0, second=0),
        )

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
                    "description": "very real image upload.",
                },
            )

        self.assertEqual(image.id, "private/1337")
        self.assertEqual(image.label, "Realest Image Upload")
        self.assertEqual(image.description, "very real image upload.")
        self.assertEqual(image.capabilities[0], "cloud-init")

        self.assertEqual(url, "https://linode.com/")

    def test_image_upload(self):
        """
        Test that an image can be uploaded.
        """

        def put_mock(url: str, data: BinaryIO = None, **kwargs):
            self.assertEqual(url, "https://linode.com/")
            self.assertEqual(data.read(), TEST_IMAGE_CONTENT)

        with patch("requests.put", put_mock), self.mock_post("/images/upload"):
            image = self.client.image_upload(
                "Realest Image Upload",
                "us-southeast",
                BytesIO(TEST_IMAGE_CONTENT),
                description="very real image upload.",
            )

        self.assertEqual(image.id, "private/1337")
        self.assertEqual(image.label, "Realest Image Upload")
        self.assertEqual(image.description, "very real image upload.")

    def test_image_create_cloud_init(self):
        """
        Test that an image can be created successfully with cloud-init.
        """

        with self.mock_post("images/private/123") as m:
            self.client.images.create(
                "Test Image",
                "us-southeast",
                description="very real image upload.",
                cloud_init=True,
            )

            self.assertTrue(m.call_data["cloud_init"])

    def test_image_create_upload_cloud_init(self):
        """
        Test that an image upload URL can be created successfully with cloud-init.
        """

        with self.mock_post("images/upload") as m:
            self.client.images.create_upload(
                "Test Image",
                "us-southeast",
                description="very real image upload.",
                cloud_init=True,
            )

            self.assertTrue(m.call_data["cloud_init"])

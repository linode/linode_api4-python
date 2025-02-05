from datetime import datetime
from io import BytesIO
from test.unit.base import ClientBaseCase
from typing import BinaryIO, Optional
from unittest.mock import patch

from linode_api4.objects import Image, Region

# A minimal gzipped image that will be accepted by the API
TEST_IMAGE_CONTENT = (
    b"\x1f\x8b\x08\x08\xbd\x5c\x91\x60\x00\x03\x74\x65\x73\x74\x2e\x69"
    b"\x6d\x67\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00"
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

        self.assertEqual(image.tags[0], "tests")
        self.assertEqual(image.total_size, 1100)
        self.assertEqual(image.regions[0].region, "us-east")
        self.assertEqual(image.regions[0].status, "available")

    def test_image_create_upload(self):
        """
        Test that an image upload URL can be created successfully.
        """

        with self.mock_post("/images/upload") as m:
            image, url = self.client.image_create_upload(
                "Realest Image Upload",
                "us-southeast",
                description="very real image upload.",
                tags=["test_tag", "test2"],
            )

            self.assertEqual(m.call_url, "/images/upload")
            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_data,
                {
                    "label": "Realest Image Upload",
                    "region": "us-southeast",
                    "description": "very real image upload.",
                    "tags": ["test_tag", "test2"],
                },
            )

        self.assertEqual(image.id, "private/1337")
        self.assertEqual(image.label, "Realest Image Upload")
        self.assertEqual(image.description, "very real image upload.")
        self.assertEqual(image.capabilities[0], "cloud-init")
        self.assertEqual(image.tags[0], "test_tag")
        self.assertEqual(image.tags[1], "test2")

        self.assertEqual(url, "https://linode.com/")

    def test_image_upload(self):
        """
        Test that an image can be uploaded.
        """

        def put_mock(url: str, data: Optional[BinaryIO] = None, **kwargs):
            self.assertEqual(url, "https://linode.com/")
            self.assertEqual(data.read(), TEST_IMAGE_CONTENT)

        with patch("requests.put", put_mock), self.mock_post("/images/upload"):
            image = self.client.image_upload(
                "Realest Image Upload",
                "us-southeast",
                BytesIO(TEST_IMAGE_CONTENT),
                description="very real image upload.",
                tags=["test_tag", "test2"],
            )

        self.assertEqual(image.id, "private/1337")
        self.assertEqual(image.label, "Realest Image Upload")
        self.assertEqual(image.description, "very real image upload.")
        self.assertEqual(image.tags[0], "test_tag")
        self.assertEqual(image.tags[1], "test2")

    def test_image_replication(self):
        """
        Test that image can be replicated.
        """

        replication_url = "/images/private/123/regions"
        regions = ["us-east", Region(self.client, "us-west")]
        with self.mock_post(replication_url) as m:
            image = Image(self.client, "private/123")
            image.replicate(regions)

            self.assertEqual(replication_url, m.call_url)
            self.assertEqual(
                m.call_data,
                {"regions": ["us-east", "us-west"]},
            )

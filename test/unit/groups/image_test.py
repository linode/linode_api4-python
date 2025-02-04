from test.unit.base import ClientBaseCase


class ImageTest(ClientBaseCase):
    """
    Tests methods of the Image class
    """

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

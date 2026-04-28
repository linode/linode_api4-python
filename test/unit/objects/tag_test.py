from test.unit.base import ClientBaseCase, MethodMock

from linode_api4.objects import Tag
from linode_api4.objects.networking import ReservedIPAddress


class TagTest(ClientBaseCase):
    """
    Tests methods of the Tag class
    """

    def test_get_tag(self):
        """
        Tests that Tag is loaded correctly by label
        """
        tag = Tag(self.client, "something")

        self.assertEqual(tag.label, "something")
        self.assertFalse(hasattr(tag, "_raw_objects"))

    def test_load_tag(self):
        """
        Tests that the LinodeClient can load a tag
        """
        tag = self.client.load(Tag, "something")

        self.assertEqual(tag.label, "something")
        self.assertTrue(hasattr(tag, "_raw_objects"))  # got the raw objects
        print(tag._raw_objects)

        # objects loaded up right
        self.assertEqual(len(tag.objects), 1)
        self.assertEqual(tag.objects[0].id, 123)
        self.assertEqual(tag.objects[0].label, "linode123")
        self.assertEqual(tag.objects[0].tags, ["something"])

    def test_delete_tag(self):
        """
        Tests that you can delete a tag
        """
        with self.mock_delete() as m:
            tag = Tag(self.client, "nothing")
            result = tag.delete()

            self.assertEqual(result, True)

            self.assertEqual(m.call_url, "/tags/nothing")

    def test_tagged_reserved_ipv4_address(self):
        """
        Tests that a tagged reserved_ipv4_address object is correctly resolved
        to a ReservedIPAddress instance.
        """
        with self.mock_get(
            {
                "page": 1,
                "pages": 1,
                "results": 1,
                "data": [
                    {
                        "type": "reserved_ipv4_address",
                        "data": {
                            "address": "66.175.209.100",
                            "gateway": "66.175.209.1",
                            "linode_id": None,
                            "prefix": 24,
                            "public": True,
                            "rdns": "66-175-209-100.ip.linodeusercontent.com",
                            "region": "us-east",
                            "reserved": True,
                            "subnet_mask": "255.255.255.0",
                            "tags": ["lb"],
                            "type": "ipv4",
                        },
                    }
                ],
            }
        ):
            tag = self.client.load(Tag, "lb")
            objects = tag.objects

            self.assertEqual(len(objects), 1)
            self.assertIsInstance(objects[0], ReservedIPAddress)
            self.assertEqual(objects[0].address, "66.175.209.100")
            self.assertEqual(objects[0].region.id, "us-east")
            self.assertTrue(objects[0].reserved)
            self.assertEqual(objects[0].tags, ["lb"])

    def test_create_tag_with_reserved_ipv4_addresses(self):
        """
        Tests that creating a tag with reserved_ipv4_addresses sends them in
        the request body.
        """
        with MethodMock("post", {"label": "lb"}) as m:
            self.client.tags.create(
                "lb", reserved_ipv4_addresses=["66.175.209.100"]
            )

            body = m.call_data
            self.assertEqual(body["label"], "lb")
            self.assertEqual(
                body["reserved_ipv4_addresses"], ["66.175.209.100"]
            )

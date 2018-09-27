from datetime import datetime
from test.base import ClientBaseCase

from linode_api4.objects import Instance, Tag


class TagTest(ClientBaseCase):
    """
    Tests methods of the Tag class
    """
    def test_get_tag(self):
        """
        Tests that Tag is loaded correctly by label
        """
        tag = Tag(self.client, 'something')

        self.assertEqual(tag.label, "something")
        self.assertFalse(hasattr(tag, '_raw_objects'))

    def test_load_tag(self):
        """
        Tests that the LinodeClient can load a tag
        """
        tag = self.client.load(Tag, 'something')

        self.assertEqual(tag.label, 'something')
        self.assertTrue(hasattr(tag, '_raw_objects')) # got the raw objects
        print(tag._raw_objects)

        # objects loaded up right
        self.assertEqual(len(tag.objects), 1)
        self.assertEqual(tag.objects[0].id, 123)
        self.assertEqual(tag.objects[0].label, 'linode123')
        self.assertEqual(tag.objects[0].tags, ['something'])

    def test_delete_tag(self):
        """
        Tests that you can delete a tag
        """
        with self.mock_delete() as m:
            tag = Tag(self.client, 'nothing')
            result = tag.delete()

            self.assertEqual(result, True)

            self.assertEqual(m.call_url, '/tags/nothing')

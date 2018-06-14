from test.base import ClientBaseCase

from linode_api.objects import Type


class LinodeTypeTest(ClientBaseCase):
    def test_get_types(self):
        """
        Tests that Linode types can be returned
        """
        types = self.client.linode.types()

        self.assertEqual(len(types), 4)
        for t in types:
            self.assertTrue(t._populated)
            self.assertIsNotNone(t.id)
            self.assertIsNotNone(t.label)
            self.assertIsNotNone(t.disk)

    def test_get_type_by_id(self):
        """
        Tests that a Linode type is loaded correctly by ID
        """
        t = Type(self.client, 'g5-nanode-1')
        self.assertEqual(t._populated, False)

        self.assertEqual(t.vcpus, 1)
        self.assertEqual(t.label, "Linode 1024")
        self.assertEqual(t.disk, 20480)

from test.base import ClientBaseCase

class LinodeClientGeneralTest(ClientBaseCase):
    """
    Tests methods of the LinodeClient class that do not live inside of a group.
    """
    def test_get_regions(self):
        r = self.client.get_regions()

        self.assertEqual(len(r), 9)
        for region in r:
            self.assertTrue(region._populated)
            self.assertIsNotNone(region.id)
            self.assertIsNotNone(region.country)


class LinodeGroupTest(ClientBaseCase):
    """
    Tests methods of the LinodeGroup
    """
    def test_create_linode(self):
        """
        Tests that a Linode can be created successfully
        """
        with self.mock_post('linodes/123') as m:
            l = self.client.linode.create_instance('us-east-1a', 'g5-standard-1')

            self.assertIsNotNone(l)
            self.assertEqual(l.id, 123)
            #
            #self.assertEqual(m.call_data, {
            #    "region": "us-east-1a",
            #    "type": "g5-standard-1"
            #})

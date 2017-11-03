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
        with self.mock_post('linode/instances/123') as m:
            l = self.client.linode.create_instance('g5-standard-1', 'us-east-1a')

            self.assertIsNotNone(l)
            self.assertEqual(l.id, 123)

            self.assertEqual(m.call_url, '/linode/instances')

            self.assertEqual(m.call_data, {
                "region": "us-east-1a",
                "type": "g5-standard-1"
            })

            r = l.region

            # assert that lazy-loaded relationships work
            self.assertIsNotNone(r)
            self.assertEqual(r._populated, False)
            self.assertEqual(r.country, 'us')
            self.assertEqual(r._populated, True)

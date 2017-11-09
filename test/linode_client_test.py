from test.base import ClientBaseCase

from linode.objects import LongviewClient


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

class LongviewGroupTest(ClientBaseCase):
    """
    Tests methods of the LongviewGroup
    """
    def test_get_clients(self):
        """
        Tests that a list of LongviewClients can be retrieved
        """
        r = self.client.longview.get_clients()

        self.assertEqual(len(r), 2)
        self.assertEqual(r[0].label, "test_client_1")
        self.assertEqual(r[0].id, 1234)
        self.assertEqual(r[1].label, "longview5678")
        self.assertEqual(r[1].id, 5678)


    def test_create_client(self):
        """
        Tests that creating a client calls the api correctly
        """
        with self.mock_post('longview/clients/5678') as m:
            client = self.client.longview.create_client()

            self.assertIsNotNone(client)
            self.assertEqual(client.id, 5678)
            self.assertEqual(client.label, 'longview5678')

            self.assertEqual(m.call_url, '/longview/clients')
            self.assertEqual(m.call_data, {})


    def test_create_client_with_label(self):
        """
        Tests that creating a client with a label calls the api correctly
        """
        with self.mock_post('longview/clients/1234') as m:
            client = self.client.longview.create_client(label='test_client_1')

            self.assertIsNotNone(client)
            self.assertEqual(client.id, 1234)
            self.assertEqual(client.label, 'test_client_1')

            self.assertEqual(m.call_url, '/longview/clients')
            self.assertEqual(m.call_data, {"label": "test_client_1"})

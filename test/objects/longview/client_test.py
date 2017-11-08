from datetime import datetime

from test.base import ClientBaseCase
from linode.objects.base import MappedObject

from linode.objects import LongviewClient


class LongviewClientTest(ClientBaseCase):
    """
    Tests methods of the LongviewClient class
    """
    def test_get_client(self):
        """
        Tests that a client is loaded correctly by ID
        """
        client = LongviewClient(self.client, 1234)
        self.assertEqual(client._populated, False)

        self.assertEqual(client.label, 'test_client_1')
        self.assertEqual(client._populated, True)

        self.assertIsInstance(client.created, datetime)
        self.assertIsInstance(client.updated, datetime)

        self.assertIsInstance(client.apps, MappedObject)
        self.assertFalse(client.apps.nginx)
        self.assertFalse(client.apps.mysql)
        self.assertFalse(client.apps.apache)

        self.assertEqual(client.install_code, '12345678-ABCD-EF01-23456789ABCDEF12')
        self.assertEqual(client.api_key, '12345678-ABCD-EF01-23456789ABCDEF12')

    def test_update_label(self):
        """
        Tests that updating a client's label contacts the api correctly.
        """
        with self.mock_put('longview/clients/1234') as m:
            client = LongviewClient(self.client, 1234)
            client.label = "updated"
            client.save()

            self.assertEqual(m.call_url, '/longview/clients/1234')
            self.assertEqual(m.call_data, {
                "label": "updated"
            })

    def test_delete_client(self):
        """
        Tests that deleting a client creates the correct api request.
        """
        with self.mock_delete() as m:
            client = LongviewClient(self.client, 1234)
            client.delete()

            self.assertEqual(m.call_url, '/longview/clients/1234')

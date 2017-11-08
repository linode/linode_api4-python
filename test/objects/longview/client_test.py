from test.base import ClientBaseCase

from linode.objects import LongviewClient


class LongviewClientTest(ClientBaseCase):
    """
    Tests methods of the LongviewClient class
    """
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

from test.base import ClientBaseCase
from linode.objects.base import MappedObject

from linode.objects import LongviewSubscription


class LongviewSubscriptionTest(ClientBaseCase):
    """
    Tests methods of the LongviewSubscription class
    """
    def test_get_subscription(self):
        """
        Tests that a subscription is loaded correctly by ID
        """
        sub = LongviewSubscription(self.client, "longview-40")
        self.assertEqual(sub._populated, False)

        self.assertEqual(sub.label, 'Longview Pro 40 pack')
        self.assertEqual(sub._populated, True)

        self.assertEqual(sub.clients_included, 40)

        self.assertIsInstance(sub.price, MappedObject)
        self.assertEqual(sub.price.hourly, .15)
        self.assertEqual(sub.price.monthly, 100)

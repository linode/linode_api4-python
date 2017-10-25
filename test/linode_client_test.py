from test.base import ClientBaseCase

class LinodeClientGeneralTest(ClientBaseCase):
    """
    Tests methods of the LinodeClient class that do not live inside of a group.
    """
    def test_GET_regions(self):
        r = self.client.get_regions()

        self.assertEqual(len(r), 9)
        for region in r:
            self.assertTrue(region._populated)
            self.assertIsNotNone(region.id)
            self.assertIsNotNone(region.country)

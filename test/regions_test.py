from test.base import ClientBaseCase

class RegionsTest(ClientBaseCase):
    def test_GET_regions(self):
        r = self.client.get_regions()

        self.assertEqual(len(r), 9)

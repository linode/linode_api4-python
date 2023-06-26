from test.unit.base import ClientBaseCase

from linode_api4.objects import Region


class RegionTest(ClientBaseCase):
    """
    Tests methods of the Region class
    """

    def test_get_region(self):
        """
        Tests that a Region is loaded correctly by ID
        """
        region = Region(self.client, "us-east")

        self.assertEqual(region.id, "us-east")
        self.assertIsNotNone(region.capabilities)
        self.assertEqual(region.country, "us")
        self.assertEqual(region.label, "label7")
        self.assertEqual(region.status, "ok")
        self.assertIsNotNone(region.resolvers)

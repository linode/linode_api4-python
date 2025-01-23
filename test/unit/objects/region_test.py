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
        self.assertEqual(region.site_type, "core")
        self.assertEqual(
            region.placement_group_limits.maximum_pgs_per_customer, 5
        )
        self.assertEqual(
            region.placement_group_limits.maximum_linodes_per_pg, 5
        )

    def test_region_availability(self):
        """
        Tests that availability for a specific region can be listed and filtered on.
        """
        avail_entries = Region(self.client, "us-east").availability

        for entry in avail_entries:
            assert entry.region is not None
            assert len(entry.region) > 0

            assert entry.plan is not None
            assert len(entry.plan) > 0

            assert entry.available is not None

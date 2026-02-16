import json
from test.unit.base import ClientBaseCase

from linode_api4.objects.region import RegionAvailabilityEntry


class RegionTest(ClientBaseCase):
    """
    Tests methods of the Region class
    """

    def test_list_availability(self):
        """
        Tests that region availability can be listed and filtered on.
        """

        with self.mock_get("/regions/availability") as m:
            avail_entries = self.client.regions.availability(
                RegionAvailabilityEntry.filters.region == "us-east",
                RegionAvailabilityEntry.filters.plan == "premium4096.7",
            )

            assert len(avail_entries) > 0

            for entry in avail_entries:
                assert len(entry.region) > 0
                assert len(entry.plan) > 0
                assert entry.available is not None

            # Ensure all three pages are read
            assert m.call_count == 3
            assert m.mock.call_args_list[0].args[0] == "//regions/availability"

            assert (
                m.mock.call_args_list[1].args[0]
                == "//regions/availability?page=2&page_size=100"
            )
            assert (
                m.mock.call_args_list[2].args[0]
                == "//regions/availability?page=3&page_size=100"
            )

            # Ensure the filter headers are correct
            for k, call in m.mock.call_args_list:
                assert json.loads(call.get("headers").get("X-Filter")) == {
                    "+and": [{"region": "us-east"}, {"plan": "premium4096.7"}]
                }

    def test_list_vpc_availability(self):
        """
        Tests that region VPC availability can be listed.
        """

        with self.mock_get("/regions/vpc-availability") as m:
            vpc_entries = self.client.regions.vpc_availability()

            assert len(vpc_entries) > 0

            for entry in vpc_entries:
                assert len(entry.region) > 0
                assert entry.available is not None
                # available_ipv6_prefix_lengths may be empty list but should exist
                assert entry.available_ipv6_prefix_lengths is not None

            # Ensure both pages are read
            assert m.call_count == 2
            assert (
                m.mock.call_args_list[0].args[0] == "//regions/vpc-availability"
            )

            assert (
                m.mock.call_args_list[1].args[0]
                == "//regions/vpc-availability?page=2&page_size=25"
            )

    def test_get_vpc_availability(self):
        """
        Tests that VPC availability for a specific region can be retrieved.
        """

        with self.mock_get("/regions/us-east/vpc-availability") as m:
            vpc_avail = self.client.regions.vpc_availability_get("us-east")

            assert vpc_avail is not None
            assert vpc_avail.region == "us-east"
            assert vpc_avail.available is True
            assert vpc_avail.available_ipv6_prefix_lengths == [52, 48]

    def test_get_availability(self):
        """
        Tests that availability for a specific region can be retrieved.
        """

        with self.mock_get("/regions/us-east/availability") as m:
            avail_entries = self.client.regions.availability_get("us-east")

            assert len(avail_entries) > 0

            # Verify first entry to ensure deserialization works
            first_entry = avail_entries[0]
            assert first_entry.region == "us-east"
            assert len(first_entry.plan) > 0
            assert first_entry.available is not None

import pytest

from linode_api4.objects import Region
from linode_api4.objects.region import RegionVPCAvailability


@pytest.mark.smoke
def test_list_regions_vpc_availability(test_linode_client):
    """
    Test listing VPC availability for all regions.
    """
    client = test_linode_client

    vpc_availability = client.regions.vpc_availability()

    assert len(vpc_availability) > 0

    for entry in vpc_availability:
        assert entry.region is not None
        assert len(entry.region) > 0
        assert entry.available is not None
        assert isinstance(entry.available, bool)
        # available_ipv6_prefix_lengths may be empty list but should exist
        assert entry.available_ipv6_prefix_lengths is not None
        assert isinstance(entry.available_ipv6_prefix_lengths, list)


@pytest.mark.smoke
def test_get_region_vpc_availability_via_group(test_linode_client):
    """
    Test getting VPC availability for a specific region via RegionGroup.
    """
    client = test_linode_client

    # Get the first available region
    regions = client.regions()
    assert len(regions) > 0
    test_region_id = regions[0].id

    vpc_avail = client.regions.vpc_availability_get(test_region_id)

    assert vpc_avail is not None
    assert vpc_avail.region == test_region_id
    assert vpc_avail.available is not None
    assert isinstance(vpc_avail.available, bool)
    assert vpc_avail.available_ipv6_prefix_lengths is not None
    assert isinstance(vpc_avail.available_ipv6_prefix_lengths, list)


@pytest.mark.smoke
def test_get_region_vpc_availability_via_object(test_linode_client):
    """
    Test getting VPC availability via the Region object property.
    """
    client = test_linode_client

    # Get the first available region
    regions = client.regions()
    assert len(regions) > 0
    test_region_id = regions[0].id

    region = Region(client, test_region_id)
    vpc_avail = region.vpc_availability

    assert vpc_avail is not None
    assert vpc_avail.region == test_region_id
    assert vpc_avail.available is not None
    assert isinstance(vpc_avail.available, bool)
    assert vpc_avail.available_ipv6_prefix_lengths is not None
    assert isinstance(vpc_avail.available_ipv6_prefix_lengths, list)


@pytest.mark.smoke
def test_get_region_availability_via_group(test_linode_client):
    """
    Test getting availability for a specific region via RegionGroup.
    """
    client = test_linode_client

    # Get the first available region
    regions = client.regions()
    assert len(regions) > 0
    test_region_id = regions[0].id

    avail_entries = client.regions.availability_get(test_region_id)

    assert len(avail_entries) > 0

    for entry in avail_entries:
        assert entry.region == test_region_id
        assert entry.plan is not None
        assert len(entry.plan) > 0
        assert entry.available is not None
        assert isinstance(entry.available, bool)


def test_vpc_availability_matches_region_id(test_linode_client):
    """
    Test that VPC availability region field matches the requested region.
    """
    client = test_linode_client

    # Test with a known region
    region_id = "us-east"
    vpc_avail = client.regions.vpc_availability_get(region_id)

    assert vpc_avail.region == region_id


def test_vpc_availability_available_regions(test_linode_client):
    """
    Test that some regions have VPC availability enabled.
    """
    client = test_linode_client

    vpc_availability = client.regions.vpc_availability()

    # Filter for regions where VPC is available
    available_regions = [v for v in vpc_availability if v.available]

    # There should be at least some regions with VPC available
    assert len(available_regions) > 0

    # Check that available regions have proper data
    for entry in available_regions:
        assert entry.region is not None
        assert entry.available is True


def test_vpc_availability_pagination(test_linode_client):
    """
    Test that VPC availability listing returns all entries.
    """
    client = test_linode_client

    # Get all VPC availability entries
    all_entries = client.regions.vpc_availability()

    # Verify we got results
    assert len(all_entries) > 0

    # Each entry should have required fields
    for entry in all_entries:
        assert entry.region is not None
        assert entry.available is not None
        assert entry.available_ipv6_prefix_lengths is not None


def test_vpc_availability_list_complete(test_linode_client):
    """
    Test that vpc_availability endpoint returns complete list of all regions.
    """
    client = test_linode_client

    # Get VPC availability for all regions
    vpc_availability = client.regions.vpc_availability()

    # Get all regions
    all_regions = client.regions()

    # VPC availability should contain entries for all regions
    assert len(vpc_availability) == len(all_regions)

    # Verify each region has a VPC availability entry
    vpc_region_ids = {v.region for v in vpc_availability}
    all_region_ids = {r.id for r in all_regions}

    assert vpc_region_ids == all_region_ids

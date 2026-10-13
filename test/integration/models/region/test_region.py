import pytest

from linode_api4.objects import Region


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

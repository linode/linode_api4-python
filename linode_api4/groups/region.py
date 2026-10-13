from linode_api4.groups import Group
from linode_api4.objects import Region
from linode_api4.objects.region import (
    RegionAvailabilityEntry,
    RegionVPCAvailability,
)


class RegionGroup(Group):
    def __call__(self, *filters):
        """
        Returns the available Regions for Linode products.

        This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           region = client.regions()

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-regions

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of available Regions.
        :rtype: PaginatedList of Region
        """

        return self.client._get_and_filter(Region, *filters)

    def availability(self, *filters):
        """
        Returns the availability of Linode plans within a Region.


        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-regions-availability

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of entries describing the availability of a plan in a region.
        :rtype: PaginatedList of RegionAvailabilityEntry
        """

        return self.client._get_and_filter(
            RegionAvailabilityEntry, *filters, endpoint="/regions/availability"
        )

    def vpc_availability(self, *filters):
        """
        Returns VPC availability data for all regions.

        NOTE: IPv6 VPCs may not currently be available to all users.

        This endpoint supports pagination with the following parameters:
        - page: Page number (>= 1)
        - page_size: Number of items per page (25-500)

        Pagination is handled automatically by PaginatedList. To configure page_size,
        set it when creating the LinodeClient:

            client = LinodeClient(token, page_size=100)

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-regions-vpc-availability

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of VPC availability data for regions.
        :rtype: PaginatedList of RegionVPCAvailability
        """

        return self.client._get_and_filter(
            RegionVPCAvailability,
            *filters,
            endpoint="/regions/vpc-availability",
        )

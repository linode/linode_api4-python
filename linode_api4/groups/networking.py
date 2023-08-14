from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import (
    VLAN,
    Base,
    Firewall,
    Instance,
    IPAddress,
    IPv6Pool,
    IPv6Range,
    Region,
)


class NetworkingGroup(Group):
    """
    Collections related to Linode Networking.
    """

    def firewalls(self, *filters):
        """
        Retrieves the Firewalls your user has access to.

        API Documentation: https://www.linode.com/docs/api/networking/#firewalls-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Firewalls the acting user can access.
        :rtype: PaginatedList of Firewall
        """
        return self.client._get_and_filter(Firewall, *filters)

    def firewall_create(self, label, rules, **kwargs):
        """
        Creates a new Firewall, either in the given Region or
        attached to the given Instance.

        API Documentation: https://www.linode.com/docs/api/networking/#firewall-create

        :param label: The label for the new Firewall.
        :type label: str
        :param rules: The rules to apply to the new Firewall. For more information on Firewall rules, see our `Firewalls Documentation`_.
        :type rules: dict

        :returns: The new Firewall.
        :rtype: Firewall

        Example usage::

           rules = {
                'outbound': [
                    {
                        'action': 'ACCEPT',
                        'addresses': {
                            'ipv4': [
                                '0.0.0.0/0'
                            ],
                            'ipv6': [
                                "ff00::/8"
                            ]
                        },
                        'description': 'Allow HTTP out.',
                        'label': 'allow-http-out',
                        'ports': '80',
                        'protocol': 'TCP'
                    }
                ],
                'outbound_policy': 'DROP',
                'inbound': [],
                'inbound_policy': 'DROP'
            }

            firewall = client.networking.firewall_create('my-firewall', rules)

        .. _Firewalls Documentation: https://www.linode.com/docs/api/networking/#firewall-create__request-body-schema
        """

        params = {
            "label": label,
            "rules": rules,
        }
        params.update(kwargs)

        result = self.client.post("/networking/firewalls", data=params)

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating Firewall!", json=result
            )

        f = Firewall(self.client, result["id"], result)
        return f

    def ips(self, *filters):
        """
        Returns a list of IP addresses on this account, excluding private addresses.

        API Documentation: https://www.linode.com/docs/api/networking/#ip-addresses-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of IP addresses on this account.
        :rtype: PaginatedList of IPAddress
        """
        return self.client._get_and_filter(IPAddress, *filters)

    def ipv6_ranges(self, *filters):
        """
        Returns a list of IPv6 ranges on this account.

        API Documentation: https://www.linode.com/docs/api/networking/#ipv6-ranges-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of IPv6 ranges on this account.
        :rtype: PaginatedList of IPv6Range
        """
        return self.client._get_and_filter(IPv6Range, *filters)

    def ipv6_pools(self, *filters):
        """
        Returns a list of IPv6 pools on this account.

        API Documentation: https://www.linode.com/docs/api/networking/#ipv6-pools-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of IPv6 pools on this account.
        :rtype: PaginatedList of IPv6Pool
        """

        return self.client._get_and_filter(IPv6Pool, *filters)

    def vlans(self, *filters):
        """
        .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.

        Returns a list of VLANs on your account.

        API Documentation: https://www.linode.com/docs/api/networking/#vlans-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A List of VLANs on your account.
        :rtype: PaginatedList of VLAN
        """
        return self.client._get_and_filter(VLAN, *filters)

    def ips_assign(self, region, *assignments):
        """
        Redistributes :any:`IP Addressees<IPAddress>` within a single region.
        This function takes a :any:`Region` and a list of assignments to make,
        then requests that the assignments take place.  If any :any:`Instance`
        ends up without a public IP, or with more than one private IP, all of
        the assignments will fail.

        .. note::
           This function *does not* update the local Linode Instance objects
           when called.  In order to see the new addresses on the local
           instance objects, be sure to invalidate them with ``invalidate()``
           after this completes.

        Example usage::

           linode1 = Instance(client, 123)
           linode2 = Instance(client, 456)

           # swap IPs between linodes 1 and 2
           client.networking.assign_ips(linode1.region,
                                        linode1.ips.ipv4.public[0].to(linode2),
                                        linode2.ips.ipv4.public[0].to(linode1))

           # make sure linode1 and linode2 have updated ipv4 and ips values
           linode1.invalidate()
           linode2.invalidate()

        API Documentation: https://www.linode.com/docs/api/networking/#linodes-assign-ipv4s

        :param region: The Region in which the assignments should take place.
                       All Instances and IPAddresses involved in the assignment
                       must be within this region.
        :type region: str or Region
        :param assignments: Any number of assignments to make.  See
                            :any:`IPAddress.to` for details on how to construct
                            assignments.
        :type assignments: dct

        DEPRECATED: Use ip_addresses_assign() instead
        """
        for a in assignments:
            if not "address" in a or not "linode_id" in a:
                raise ValueError("Invalid assignment: {}".format(a))
        if isinstance(region, Region):
            region = region.id

        self.client.post(
            "/networking/ipv4/assign",
            data={
                "region": region,
                "assignments": assignments,
            },
        )

    def ip_allocate(self, linode, public=True):
        """
        Allocates an IP to a Instance you own.  Additional IPs must be requested
        by opening a support ticket first.

        API Documentation: https://www.linode.com/docs/api/networking/#ip-address-allocate

        :param linode: The Instance to allocate the new IP for.
        :type linode: Instance or int
        :param public: If True, allocate a public IP address.  Defaults to True.
        :type public: bool

        :returns: The new IPAddress.
        :rtype: IPAddress
        """
        result = self.client.post(
            "/networking/ips/",
            data={
                "linode_id": linode.id if isinstance(linode, Base) else linode,
                "type": "ipv4",
                "public": public,
            },
        )

        if not "address" in result:
            raise UnexpectedResponseError(
                "Unexpected response when adding IPv4 address!", json=result
            )

        ip = IPAddress(self.client, result["address"], result)
        return ip

    def ips_share(self, linode, *ips):
        """
        Shares the given list of :any:`IPAddresses<IPAddress>` with the provided
        :any:`Instance`.  This will enable the provided Instance to bring up the
        shared IP Addresses even though it does not own them.

        API Documentation: https://www.linode.com/docs/api/networking/#ipv4-sharing-configure

        :param linode: The Instance to share the IPAddresses with.  This Instance
                       will be able to bring up the given addresses.
        :type: linode: int or Instance
        :param ips: Any number of IPAddresses to share to the Instance.
        :type ips: str or IPAddress

        DEPRECATED: Use ip_addresses_share() instead
        """
        if not isinstance(linode, Instance):
            # make this an object
            linode = Instance(self.client, linode)

        params = []
        for ip in ips:
            if isinstance(ip, str):
                params.append(ip)
            elif isinstance(ip, IPAddress):
                params.append(ip.address)
            else:
                params.append(str(ip))  # and hope that works

        params = {"ips": params}

        self.client.post(
            "{}/networking/ipv4/share".format(Instance.api_endpoint),
            model=linode,
            data=params,
        )

        linode.invalidate()  # clear the Instance's shared IPs

    def ip_addresses_share(self, ips, linode):
        """
        Configure shared IPs. IP sharing allows IP address reassignment
        (also referred to as IP failover) from one Linode to another if the
        primary Linode becomes unresponsive. This means that requests to the primary Linode’s
        IP address can be automatically rerouted to secondary Linodes at the configured shared IP addresses.

        API Documentation: https://www.linode.com/docs/api/networking/#ip-addresses-share

        :param linode: The id of the Instance or the Instance to share the IPAddresses with.
                          This Instance will be able to bring up the given addresses.
        :type: linode: int or Instance
        :param ips: Any number of IPAddresses to share to the Instance. Enter an empty array to
                    remove all shared IP addresses.
        :type ips: str or IPAddress
        """

        shared_ips = []
        for ip in ips:
            if isinstance(ip, str):
                shared_ips.append(ip)
            elif isinstance(ip, IPAddress):
                shared_ips.append(ip.address)
            else:
                shared_ips.append(str(ip))  # and hope that works

        params = {
            "ips": shared_ips,
            "linode_id": linode
            if not isinstance(linode, Instance)
            else linode.id,
        }

        self.client.post("/networking/ips/share", model=self, data=params)

    def ip_addresses_assign(self, assignments, region):
        """
        Assign multiple IPv4 addresses and/or IPv6 ranges to multiple Linodes in one Region.
        This allows swapping, shuffling, or otherwise reorganizing IPs to your Linodes.

        The following restrictions apply:
            - All Linodes involved must have at least one public IPv4 address after assignment.
            - Linodes may have no more than one assigned private IPv4 address.
            - Linodes may have no more than one assigned IPv6 range.


        :param region: The Region in which the assignments should take place.
                       All Instances and IPAddresses involved in the assignment
                       must be within this region.
        :type region: str or Region
        :param assignments: Any number of assignments to make.  See
                            :any:`IPAddress.to` for details on how to construct
                            assignments.
        :type assignments: dct
        """

        for a in assignments["assignments"]:
            if not "address" in a or not "linode_id" in a:
                raise ValueError("Invalid assignment: {}".format(a))

        if isinstance(region, Region):
            region = region.id

        params = {"assignments": assignments, "region": region}

        self.client.post("/networking/ips/assign", model=self, data=params)

from linode_api4.groups import Group
from linode_api4.objects import MappedObject


class MaintenanceGroup(Group):
    """
    Collections related to Maintenance.
    """

    def maintenance_policies(self):
        """
        .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.

        Returns a collection of MaintenancePolicy objects representing
        available maintenance policies that can be applied to Linodes

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-maintenance-policies

        :returns: A list of Maintenance Policies that can be applied to Linodes
        :rtype: List of MaintenancePolicy objects as MappedObjects
        """

        result = self.client.get("/maintenance/policies", model=self)

        return [MappedObject(**r) for r in result["data"]]

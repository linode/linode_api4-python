from linode_api4.groups import Group
from linode_api4.objects import MappedObject


class MaintenanceGroup(Group):
    """
    Collections related to Maintenance.
    """

    def maintenance_policies(self):
        """
        Returns a collection of MaintenancePolicy objects representing
        available maintenance policies that can be applied to Linodes

        API Documentation: TODO

        :returns: A list of Maintenance Policies that can be applied to Linodes
        :rtype: List of MaintenancePolicy objects as MappedObjects
        """

        result = self.client.get("/maintenance/policies", model=self)

        return [MappedObject(**r) for r in result["data"]]

from linode_api4 import MappedObject
from linode_api4.groups import Group


class MaintenanceGroup(Group):
    def maintenance_policies(self):
        """
        Returns a collection of MaintenancePolicy objects representing
        available maintenance policies that can be applied to Linodes

        API Documentation: TODO

        :returns: A list of Maintenance Policies that can be applied to Linodes
        :rtype: List of MaintenancePolicy objects as MappedObjects
        """

        result = self.client.get("/maintenance/policies", model=self)

        return [MappedObject(**r) for r in result]

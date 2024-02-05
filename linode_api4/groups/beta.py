from linode_api4.groups import Group
from linode_api4.objects import BetaProgram


class BetaProgramGroup(Group):
    """
    This group encapsulates all endpoints under /betas, including viewing
    available active beta programs.
    """

    def betas(self, *filters):
        """
        Returns a list of available active Beta Programs.

        API Documentation: https://www.linode.com/docs/api/beta-programs/#beta-programs-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Beta Programs that matched the query.
        :rtype: PaginatedList of BetaProgram
        """
        return self.client._get_and_filter(BetaProgram, *filters)

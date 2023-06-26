from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import Domain


class DomainGroup(Group):
    def __call__(self, *filters):
        """
        Retrieves all of the Domains the acting user has access to.

        This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           domains = client.domains()

        API Documentation: https://www.linode.com/docs/api/domains/#domains-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Domains the acting user can access.
        :rtype: PaginatedList of Domain
        """
        return self.client._get_and_filter(Domain, *filters)

    def create(self, domain, master=True, **kwargs):
        """
        Registers a new Domain on the acting user's account.  Make sure to point
        your registrar to Linode's nameservers so that Linode's DNS manager will
        correctly serve your domain.

        API Documentation: https://www.linode.com/docs/api/domains/#domain-create

        :param domain: The domain to register to Linode's DNS manager.
        :type domain: str
        :param master: Whether this is a master (defaults to true)
        :type master: bool
        :param tags: A list of tags to apply to the new domain.  If any of the
                     tags included do not exist, they will be created as part of
                     this operation.
        :type tags: list[str]

        :returns: The new Domain object.
        :rtype: Domain
        """
        params = {
            "domain": domain,
            "type": "master" if master else "slave",
        }
        params.update(kwargs)

        result = self.client.post("/domains", data=params)

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating Domain!", json=result
            )

        d = Domain(self.client, result["id"], result)
        return d

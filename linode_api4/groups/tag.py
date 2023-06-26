from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import Domain, Instance, NodeBalancer, Tag, Volume


class TagGroup(Group):
    def __call__(self, *filters):
        """
        Retrieves the Tags on your account.  This may only be attempted by
        unrestricted users.

        This is intended to be called off of the :any:`LinodeClient`
        class, like this::

           tags = client.tags()

        API Documentation: https://www.linode.com/docs/api/domains/#domain-create

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Tags on the account.
        :rtype: PaginatedList of Tag
        """
        return self.client._get_and_filter(Tag, *filters)

    def create(
        self,
        label,
        instances=None,
        domains=None,
        nodebalancers=None,
        volumes=None,
        entities=[],
    ):
        """
        Creates a new Tag and optionally applies it to the given entities.

        API Documentation: https://www.linode.com/docs/api/tags/#tags-list

        :param label: The label for the new Tag
        :type label: str
        :param entities: A list of objects to apply this Tag to upon creation.
                         May only be taggable types (Linode Instances, Domains,
                         NodeBalancers, or Volumes).  These are applied *in addition
                         to* any IDs specified with ``instances``, ``domains``,
                         ``nodebalancers``, or ``volumes``, and is a convenience
                         for sending multiple entity types without sorting them
                         yourself.
        :type entities: list of Instance, Domain, NodeBalancer, and/or Volume
        :param instances: A list of Linode Instances to apply this Tag to upon
                        creation
        :type instances: list of Instance or list of int
        :param domains: A list of Domains to apply this Tag to upon
                        creation
        :type domains: list of Domain or list of int
        :param nodebalancers: A list of NodeBalancers to apply this Tag to upon
                        creation
        :type nodebalancers: list of NodeBalancer or list of int
        :param volumes: A list of Volumes to apply this Tag to upon
                        creation
        :type volumes: list of Volumes or list of int

        :returns: The new Tag
        :rtype: Tag
        """
        linode_ids, nodebalancer_ids, domain_ids, volume_ids = [], [], [], []

        # filter input into lists of ids
        sorter = zip(
            (linode_ids, nodebalancer_ids, domain_ids, volume_ids),
            (instances, nodebalancers, domains, volumes),
        )

        for id_list, input_list in sorter:
            # if we got something, we need to find its ID
            if input_list is not None:
                for cur in input_list:
                    if isinstance(cur, int):
                        id_list.append(cur)
                    else:
                        id_list.append(cur.id)

        # filter entities into id lists too
        type_map = {
            Instance: linode_ids,
            NodeBalancer: nodebalancer_ids,
            Domain: domain_ids,
            Volume: volume_ids,
        }

        for e in entities:
            if type(e) in type_map:
                type_map[type(e)].append(e.id)
            else:
                raise ValueError("Unsupported entity type {}".format(type(e)))

        # finally, omit all id lists that are empty
        params = {
            "label": label,
            "linodes": linode_ids or None,
            "nodebalancers": nodebalancer_ids or None,
            "domains": domain_ids or None,
            "volumes": volume_ids or None,
        }

        result = self.client.post("/tags", data=params)

        if not "label" in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating Tag!", json=result
            )

        t = Tag(self.client, result["label"], result)
        return t

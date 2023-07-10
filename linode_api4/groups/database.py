from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import (
    Base,
    Database,
    DatabaseEngine,
    DatabaseType,
    MySQLDatabase,
    PostgreSQLDatabase,
)


class DatabaseGroup(Group):
    """
    Encapsulates Linode Managed Databases related methods of the :any:`LinodeClient`. This
    should not be instantiated on its own, but should instead be used through
    an instance of :any:`LinodeClient`::

       client = LinodeClient(token)
       instances = client.database.instances() # use the DatabaseGroup

    This group contains all features beneath the `/databases` group in the API v4.
    """

    def types(self, *filters):
        """
        Returns a list of Linode Database-compatible Instance types.
        These may be used to create Managed Databases, or simply
        referenced to on their own. DatabaseTypes can be
        filtered to return specific types, for example::

           database_types = client.database.types(DatabaseType.deprecated == False)

        API Documentation: https://www.linode.com/docs/api/databases/#managed-database-types-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of types that match the query.
        :rtype: PaginatedList of DatabaseType
        """
        return self.client._get_and_filter(DatabaseType, *filters)

    def engines(self, *filters):
        """
        Returns a list of Linode Managed Database Engines.
        These may be used to create Managed Databases, or simply
        referenced to on their own. Engines can be filtered to
        return specific engines, for example::

           mysql_engines = client.database.engines(DatabaseEngine.engine == 'mysql')

        API Documentation: https://www.linode.com/docs/api/databases/#managed-database-engines-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of types that match the query.
        :rtype: PaginatedList of DatabaseEngine
        """
        return self.client._get_and_filter(DatabaseEngine, *filters)

    def instances(self, *filters):
        """
        Returns a list of Managed Databases active on this account.

        API Documentation: https://www.linode.com/docs/api/databases/#managed-databases-list-all

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of databases that matched the query.
        :rtype: PaginatedList of Database
        """
        return self.client._get_and_filter(Database, *filters)

    def mysql_instances(self, *filters):
        """
        Returns a list of Managed MySQL Databases active on this account.

        API Documentation: https://www.linode.com/docs/api/databases/#managed-mysql-databases-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of MySQL databases that matched the query.
        :rtype: PaginatedList of MySQLDatabase
        """
        return self.client._get_and_filter(MySQLDatabase, *filters)

    def mysql_create(self, label, region, engine, ltype, **kwargs):
        """
        Creates an :any:`MySQLDatabase` on this account with
        the given label, region, engine, and node type.  For example::

           client = LinodeClient(TOKEN)

           # look up Region and Types to use.  In this example I'm just using
           # the first ones returned.
           region = client.regions().first()
           node_type = client.database.types()[0]
           engine = client.database.engines(DatabaseEngine.engine == 'mysql')[0]

           new_database = client.database.mysql_create(
               "example-database",
               region,
               engine.id,
               type.id
            )

        API Documentation: https://www.linode.com/docs/api/databases/#managed-mysql-database-create

        :param label: The name for this cluster
        :type label: str
        :param region: The region to deploy this cluster in
        :type region: str or Region
        :param engine: The engine to deploy this cluster with
        :type engine: str or Engine
        :param ltype: The Linode Type to use for this cluster
        :type ltype: str or Type
        """

        params = {
            "label": label,
            "region": region.id if issubclass(type(region), Base) else region,
            "engine": engine.id if issubclass(type(engine), Base) else engine,
            "type": ltype.id if issubclass(type(ltype), Base) else ltype,
        }
        params.update(kwargs)

        result = self.client.post("/databases/mysql/instances", data=params)

        if "id" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating MySQL Database", json=result
            )

        d = MySQLDatabase(self.client, result["id"], result)
        return d

    def postgresql_instances(self, *filters):
        """
        Returns a list of Managed PostgreSQL Databases active on this account.

        API Documentation: https://www.linode.com/docs/api/databases/#managed-postgresql-databases-list

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of PostgreSQL databases that matched the query.
        :rtype: PaginatedList of PostgreSQLDatabase
        """
        return self.client._get_and_filter(PostgreSQLDatabase, *filters)

    def postgresql_create(self, label, region, engine, ltype, **kwargs):
        """
        Creates an :any:`PostgreSQLDatabase` on this account with
        the given label, region, engine, and node type.  For example::

           client = LinodeClient(TOKEN)

           # look up Region and Types to use.  In this example I'm just using
           # the first ones returned.
           region = client.regions().first()
           node_type = client.database.types()[0]
           engine = client.database.engines(DatabaseEngine.engine == 'postgresql')[0]

           new_database = client.database.postgresql_create(
               "example-database",
               region,
               engine.id,
               type.id
            )

        API Documentation: https://www.linode.com/docs/api/databases/#managed-postgresql-database-create

        :param label: The name for this cluster
        :type label: str
        :param region: The region to deploy this cluster in
        :type region: str or Region
        :param engine: The engine to deploy this cluster with
        :type engine: str or Engine
        :param ltype: The Linode Type to use for this cluster
        :type ltype: str or Type
        """

        params = {
            "label": label,
            "region": region.id if issubclass(type(region), Base) else region,
            "engine": engine.id if issubclass(type(engine), Base) else engine,
            "type": ltype.id if issubclass(type(ltype), Base) else ltype,
        }
        params.update(kwargs)

        result = self.client.post(
            "/databases/postgresql/instances", data=params
        )

        if "id" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating PostgreSQL Database",
                json=result,
            )

        d = PostgreSQLDatabase(self.client, result["id"], result)
        return d

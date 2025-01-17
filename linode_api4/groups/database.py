from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import (
    Database,
    DatabaseEngine,
    DatabaseType,
    MySQLDatabase,
    PostgreSQLDatabase,
    drop_null_keys,
)
from linode_api4.objects.base import _flatten_request_body_recursive


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

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-databases-types

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

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-databases-engines

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

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-databases-instances

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

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-databases-mysql-instances

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

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-databases-mysql-instances

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
            "region": region,
            "engine": engine,
            "type": ltype,
        }
        params.update(kwargs)

        result = self.client.post(
            "/databases/mysql/instances",
            data=_flatten_request_body_recursive(drop_null_keys(params)),
        )

        if "id" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating MySQL Database", json=result
            )

        d = MySQLDatabase(self.client, result["id"], result)
        return d

    def mysql_fork(self, source, restore_time, **kwargs):
        """
        Forks an :any:`MySQLDatabase` on this account with
        the given restore_time. label, region, engine, and ltype are optional.
        For example::

           client = LinodeClient(TOKEN)

           db_to_fork = client.database.mysql_instances()[0]

           new_fork = client.database.mysql_fork(
                db_to_fork.id,
                db_to_fork.updated,
                label="new-fresh-label"
           )

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-databases-mysql-instances

        :param source: The id of the source database
        :type source: int
        :param restore_time: The timestamp for the fork
        :type restore_time: datetime
        :param label: The name for this cluster
        :type label: str
        :param region: The region to deploy this cluster in
        :type region: str | Region
        :param engine: The engine to deploy this cluster with
        :type engine: str | Engine
        :param ltype: The Linode Type to use for this cluster
        :type ltype: str | Type
        """

        params = {
            "fork": {
                "source": source,
                "restore_time": restore_time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
        }
        if "ltype" in kwargs:
            params["type"] = kwargs["ltype"]
        params.update(kwargs)

        result = self.client.post(
            "/databases/mysql/instances",
            data=_flatten_request_body_recursive(drop_null_keys(params)),
        )

        if "id" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating MySQL Database", json=result
            )

        d = MySQLDatabase(self.client, result["id"], result)
        return d

    def postgresql_instances(self, *filters):
        """
        Returns a list of Managed PostgreSQL Databases active on this account.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-databases-postgre-sql-instances

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

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-databases-postgre-sql-instances

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
            "region": region,
            "engine": engine,
            "type": ltype,
        }
        params.update(kwargs)

        result = self.client.post(
            "/databases/postgresql/instances",
            data=_flatten_request_body_recursive(drop_null_keys(params)),
        )

        if "id" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating PostgreSQL Database",
                json=result,
            )

        d = PostgreSQLDatabase(self.client, result["id"], result)
        return d

    def postgresql_fork(self, source, restore_time, **kwargs):
        """
        Forks an :any:`PostgreSQLDatabase` on this account with
        the given restore_time. label, region, engine, and ltype are optional.
        For example::

           client = LinodeClient(TOKEN)

           db_to_fork = client.database.postgresql_instances()[0]

           new_fork = client.database.postgresql_fork(
                db_to_fork.id,
                db_to_fork.updated,
                label="new-fresh-label"
           )

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-databases-postgresql-instances

        :param source: The id of the source database
        :type source: int
        :param restore_time: The timestamp for the fork
        :type restore_time: datetime
        :param label: The name for this cluster
        :type label: str
        :param region: The region to deploy this cluster in
        :type region: str | Region
        :param engine: The engine to deploy this cluster with
        :type engine: str | Engine
        :param ltype: The Linode Type to use for this cluster
        :type ltype: str | Type
        """

        params = {
            "fork": {
                "source": source,
                "restore_time": restore_time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
        }
        if "ltype" in kwargs:
            params["type"] = kwargs["ltype"]
        params.update(kwargs)

        result = self.client.post(
            "/databases/postgresql/instances",
            data=_flatten_request_body_recursive(drop_null_keys(params)),
        )

        if "id" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating PostgreSQL Database",
                json=result,
            )

        d = PostgreSQLDatabase(self.client, result["id"], result)
        return d

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from linode_api4 import (
    MySQLDatabaseConfigOptions,
    PostgreSQLDatabaseConfigOptions,
    ValkeyDatabaseConfigOptions,
)
from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import (
    DATE_FORMAT,
    Database,
    DatabaseEngine,
    DatabasePrivateNetwork,
    DatabaseType,
    MySQLDatabase,
    PostgreSQLDatabase,
    ValkeyDatabase,
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

    def mysql_config_options(self):
        """
        Returns a detailed list of all the configuration options for MySQL Databases.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-databases-mysql-config

        :returns: The JSON configuration options for MySQL Databases.
        """
        return self.client.get("/databases/mysql/config", model=self)

    def postgresql_config_options(self):
        """
        Returns a detailed list of all the configuration options for PostgreSQL Databases.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-databases-postgresql-config

        :returns: The JSON configuration options for PostgreSQL Databases.
        """
        return self.client.get("/databases/postgresql/config", model=self)

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

    def mysql_create(
        self,
        label,
        region,
        engine,
        ltype,
        engine_config: Union[MySQLDatabaseConfigOptions, Dict[str, Any]] = None,
        private_network: Union[DatabasePrivateNetwork, Dict[str, Any]] = None,
        **kwargs,
    ):
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
        :param engine_config: The configuration options for this MySQL cluster
        :type engine_config: Dict[str, Any] or MySQLDatabaseConfigOptions
        :param private_network: The private network settings to use for this cluster
        :type private_network: Dict[str, Any] or DatabasePrivateNetwork
        """

        params = {
            "label": label,
            "region": region,
            "engine": engine,
            "type": ltype,
            "engine_config": engine_config,
            "private_network": private_network,
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

    def postgresql_create(
        self,
        label,
        region,
        engine,
        ltype,
        engine_config: Union[
            PostgreSQLDatabaseConfigOptions, Dict[str, Any]
        ] = None,
        private_network: Union[DatabasePrivateNetwork, Dict[str, Any]] = None,
        **kwargs,
    ):
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
        :param engine_config: The configuration options for this PostgreSQL cluster
        :type engine_config: Dict[str, Any] or PostgreSQLDatabaseConfigOptions
        :param private_network: The private network settings to use for this cluster
        :type private_network: Dict[str, Any] or DatabasePrivateNetwork
        """

        params = {
            "label": label,
            "region": region,
            "engine": engine,
            "type": ltype,
            "engine_config": engine_config,
            "private_network": private_network,
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

    def valkey_config_options(self):
        """
        Return the advanced-parameter catalog for Valkey (limited availability).

        Metadata is returned unchanged, including scalar or array ``type``
        values, enums, examples, and defaults.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-databases-valkey-config

        :returns: Configuration option metadata.
        :rtype: dict
        """
        return self.client.get("/databases/valkey/config", model=self)

    def valkey_instances(self, *filters):
        """
        List Valkey Managed Databases on this account (limited availability).

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-databases-valkey-instances

        :param filters: Filters to apply to the collection.
        :returns: The matching clusters.
        :rtype: PaginatedList of ValkeyDatabase
        """
        return self.client._get_and_filter(ValkeyDatabase, *filters)

    def valkey_create(
        self,
        label,
        region,
        engine,
        ltype,
        engine_config: Optional[
            Union[ValkeyDatabaseConfigOptions, Dict[str, Any]]
        ] = None,
        private_network: Optional[
            Union[DatabasePrivateNetwork, Dict[str, Any]]
        ] = None,
        **kwargs,
    ):
        """
        Create a Valkey Managed Database (limited availability).

        Discover available engine versions and plans using :any:`engines`
        and :any:`types`. Advanced options use flat keys, for example::

            db = client.database.valkey_create(
                "example-valkey", region, engine, node_type,
                engine_config=ValkeyDatabaseConfigOptions(
                    valkey_persistence="rdb", frequent_snapshots=True
                ),
            )

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-databases-valkey-instances

        :param label: Cluster label.
        :type label: str
        :param region: Deployment region.
        :type region: str or Region
        :param engine: Versioned engine ID.
        :type engine: str or DatabaseEngine
        :param ltype: Database node type.
        :type ltype: str or DatabaseType
        :param engine_config: Flat advanced configuration.
        :type engine_config: ValkeyDatabaseConfigOptions or dict
        :param private_network: VPC configuration.
        :type private_network: DatabasePrivateNetwork or dict
        :param kwargs: Additional API create options, such as ``cluster_size``
                      and ``allow_list``. ``ssl_connection`` must be true.
        :returns: The created cluster.
        :rtype: ValkeyDatabase
        :raises UnexpectedResponseError: If the response lacks an ID.
        """
        params = {
            "label": label,
            "region": region,
            "engine": engine,
            "type": ltype,
            "engine_config": engine_config,
            "private_network": private_network,
        }
        params.update(kwargs)
        result = self.client.post(
            "/databases/valkey/instances",
            data=_flatten_request_body_recursive(drop_null_keys(params)),
        )
        if "id" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating Valkey Database", json=result
            )
        return ValkeyDatabase(self.client, result["id"], result)

    def valkey_fork(
        self,
        source: int,
        restore_time: Optional[Union[str, datetime]] = None,
        **kwargs,
    ):
        """
        Restore a Valkey snapshot into a new cluster (limited availability).

        Use a string from the source cluster's ``available_restore_times``,
        or omit ``restore_time`` to use the latest snapshot. Unlike SQL
        engines, Valkey does not support arbitrary point-in-time recovery.
        Persistence must be enabled on the source cluster.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-databases-valkey-instances

        :param source: Source cluster ID.
        :type source: int
        :param restore_time: Exact snapshot timestamp. Strings are sent
                             unchanged; naive datetimes are UTC and aware
                             datetimes are converted to UTC.
        :type restore_time: str or datetime or None
        :param kwargs: Optional create overrides such as ``label``, ``region``,
                       ``engine``, ``ltype``, and ``engine_config``.
        :returns: The new cluster.
        :rtype: ValkeyDatabase
        :raises TypeError: If restore_time is not a string, datetime, or None.
        :raises ValueError: If both ltype and type, or a fork override, are given.
        :raises UnexpectedResponseError: If the response lacks an ID.
        """
        if "ltype" in kwargs and "type" in kwargs:
            raise ValueError("Specify only one of ltype and type")
        if "fork" in kwargs:
            raise ValueError("Use source and restore_time to specify the fork")
        if isinstance(restore_time, datetime):
            if restore_time.tzinfo is not None:
                restore_time = restore_time.astimezone(timezone.utc)
            restore_time = restore_time.strftime(DATE_FORMAT)
        elif restore_time is not None and not isinstance(restore_time, str):
            raise TypeError("restore_time must be a string, datetime, or None")

        if "ltype" in kwargs:
            kwargs["type"] = kwargs.pop("ltype")
        params = {
            **kwargs,
            "fork": {"source": source, "restore_time": restore_time},
        }
        result = self.client.post(
            "/databases/valkey/instances",
            data=_flatten_request_body_recursive(drop_null_keys(params)),
        )
        if "id" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when forking Valkey Database", json=result
            )
        return ValkeyDatabase(self.client, result["id"], result)

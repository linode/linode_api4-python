from dataclasses import dataclass, field
from typing import Optional

from deprecated import deprecated

from linode_api4.objects import (
    Base,
    DerivedBase,
    JSONObject,
    MappedObject,
    Property,
)


class DatabaseType(Base):
    """
    The type of a managed database.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-databases-type
    """

    api_endpoint = "/databases/types/{id}"

    properties = {
        "deprecated": Property(),
        "disk": Property(),
        "engines": Property(),
        "id": Property(identifier=True),
        "label": Property(),
        "memory": Property(),
        "vcpus": Property(),
        # type_class is populated from the 'class' attribute of the returned JSON
    }

    def _populate(self, json):
        """
        Allows changing the name "class" in JSON to "type_class" in python
        """
        super()._populate(json)

        if "class" in json:
            setattr(self, "type_class", json["class"])
        else:
            setattr(self, "type_class", None)


class DatabaseEngine(Base):
    """
    A managed database engine. The following database engines are available on Linode’s platform:

        - MySQL
        - PostgreSQL

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-databases-engine
    """

    api_endpoint = "/databases/engines/{id}"

    properties = {
        "id": Property(identifier=True),
        "engine": Property(),
        "version": Property(),
    }

    def invalidate(self):
        """
        Clear out cached properties.
        """

        for attr in ["_instance"]:
            if hasattr(self, attr):
                delattr(self, attr)

        Base.invalidate(self)


@deprecated(
    reason="Backups are not supported for non-legacy database clusters."
)
class DatabaseBackup(DerivedBase):
    """
    A generic Managed Database backup.

    This class is not intended to be used on its own.
    Use the appropriate subclasses for the corresponding database engine. (e.g. MySQLDatabaseBackup)
    """

    api_endpoint = ""
    derived_url_path = "backups"
    parent_id_name = "database_id"

    properties = {
        "created": Property(is_datetime=True),
        "id": Property(identifier=True),
        "label": Property(),
        "type": Property(),
    }

    def restore(self):
        """
        Restore a backup to a Managed Database on your Account.

        API Documentation:

            - MySQL: https://techdocs.akamai.com/linode-api/reference/post-databases-mysql-instance-backup-restore
            - PostgreSQL: https://techdocs.akamai.com/linode-api/reference/post-databases-postgre-sql-instance-backup-restore
        """

        return self._client.post(
            "{}/restore".format(self.api_endpoint), model=self
        )


@deprecated(
    reason="Backups are not supported for non-legacy database clusters."
)
class MySQLDatabaseBackup(DatabaseBackup):
    """
    A backup for an accessible Managed MySQL Database.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-databases-mysql-instance-backup
    """

    api_endpoint = "/databases/mysql/instances/{database_id}/backups/{id}"


@deprecated(
    reason="Backups are not supported for non-legacy database clusters."
)
class PostgreSQLDatabaseBackup(DatabaseBackup):
    """
    A backup for an accessible Managed PostgreSQL Database.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-databases-postgresql-instance-backup
    """

    api_endpoint = "/databases/postgresql/instances/{database_id}/backups/{id}"


@dataclass
class MySQLDatabaseConfigMySQLOptions(JSONObject):
    """
    MySQLDatabaseConfigMySQLOptions represents the fields in the mysql
    field of the MySQLDatabaseConfigOptions class
    """

    connect_timeout: Optional[int] = None
    default_time_zone: Optional[str] = None
    group_concat_max_len: Optional[float] = None
    information_schema_stats_expiry: Optional[int] = None
    innodb_change_buffer_max_size: Optional[int] = None
    innodb_flush_neighbors: Optional[int] = None
    innodb_ft_min_token_size: Optional[int] = None
    innodb_ft_server_stopword_table: Optional[str] = None
    innodb_lock_wait_timeout: Optional[int] = None
    innodb_log_buffer_size: Optional[int] = None
    innodb_online_alter_log_max_size: Optional[int] = None
    innodb_read_io_threads: Optional[int] = None
    innodb_rollback_on_timeout: Optional[bool] = None
    innodb_thread_concurrency: Optional[int] = None
    innodb_write_io_threads: Optional[int] = None
    interactive_timeout: Optional[int] = None
    internal_tmp_mem_storage_engine: Optional[str] = None
    max_allowed_packet: Optional[int] = None
    max_heap_table_size: Optional[int] = None
    net_buffer_length: Optional[int] = None
    net_read_timeout: Optional[int] = None
    net_write_timeout: Optional[int] = None
    sort_buffer_size: Optional[int] = None
    sql_mode: Optional[str] = None
    sql_require_primary_key: Optional[bool] = None
    tmp_table_size: Optional[int] = None
    wait_timeout: Optional[int] = None


@dataclass
class MySQLDatabaseConfigOptions(JSONObject):
    """
    MySQLDatabaseConfigOptions is used to specify
    a MySQL Database Cluster's configuration options during its creation.
    """

    mysql: Optional[MySQLDatabaseConfigMySQLOptions] = None
    binlog_retention_period: Optional[int] = None


@dataclass
class PostgreSQLDatabaseConfigPGLookoutOptions(JSONObject):
    """
    PostgreSQLDatabasePGLookoutConfigOptions represents the fields in the pglookout
    field of the PostgreSQLDatabasePGConfigOptions class
    """

    max_failover_replication_time_lag: Optional[int] = None


@dataclass
class PostgreSQLDatabaseConfigPGOptions(JSONObject):
    """
    PostgreSQLDatabasePGConfigOptions represents the fields in the pg
    field of the PostgreSQLDatabasePGConfigOptions class
    """

    autovacuum_analyze_scale_factor: Optional[float] = None
    autovacuum_analyze_threshold: Optional[int] = None
    autovacuum_max_workers: Optional[int] = None
    autovacuum_naptime: Optional[int] = None
    autovacuum_vacuum_cost_delay: Optional[int] = None
    autovacuum_vacuum_cost_limit: Optional[int] = None
    autovacuum_vacuum_scale_factor: Optional[float] = None
    autovacuum_vacuum_threshold: Optional[int] = None
    bgwriter_delay: Optional[int] = None
    bgwriter_flush_after: Optional[int] = None
    bgwriter_lru_maxpages: Optional[int] = None
    bgwriter_lru_multiplier: Optional[float] = None
    deadlock_timeout: Optional[int] = None
    default_toast_compression: Optional[str] = None
    idle_in_transaction_session_timeout: Optional[int] = None
    jit: Optional[bool] = None
    max_files_per_process: Optional[int] = None
    max_locks_per_transaction: Optional[int] = None
    max_logical_replication_workers: Optional[int] = None
    max_parallel_workers: Optional[int] = None
    max_parallel_workers_per_gather: Optional[int] = None
    max_pred_locks_per_transaction: Optional[int] = None
    max_replication_slots: Optional[int] = None
    max_slot_wal_keep_size: Optional[int] = None
    max_stack_depth: Optional[int] = None
    max_standby_archive_delay: Optional[int] = None
    max_standby_streaming_delay: Optional[int] = None
    max_wal_senders: Optional[int] = None
    max_worker_processes: Optional[int] = None
    password_encryption: Optional[str] = None
    pg_partman_bgw_interval: Optional[int] = field(
        default=None, metadata={"json_key": "pg_partman_bgw.interval"}
    )
    pg_partman_bgw_role: Optional[str] = field(
        default=None, metadata={"json_key": "pg_partman_bgw.role"}
    )
    pg_stat_monitor_pgsm_enable_query_plan: Optional[bool] = field(
        default=None,
        metadata={"json_key": "pg_stat_monitor.pgsm_enable_query_plan"},
    )
    pg_stat_monitor_pgsm_max_buckets: Optional[int] = field(
        default=None, metadata={"json_key": "pg_stat_monitor.pgsm_max_buckets"}
    )
    pg_stat_statements_track: Optional[str] = field(
        default=None, metadata={"json_key": "pg_stat_statements.track"}
    )
    temp_file_limit: Optional[int] = None
    timezone: Optional[str] = None
    track_activity_query_size: Optional[int] = None
    track_commit_timestamp: Optional[str] = None
    track_functions: Optional[str] = None
    track_io_timing: Optional[str] = None
    wal_sender_timeout: Optional[int] = None
    wal_writer_delay: Optional[int] = None


@dataclass
class PostgreSQLDatabaseConfigOptions(JSONObject):
    """
    PostgreSQLDatabaseConfigOptions is used to specify
    a PostgreSQL Database Cluster's configuration options during its creation.
    """

    pg: Optional[PostgreSQLDatabaseConfigPGOptions] = None
    pg_stat_monitor_enable: Optional[bool] = None
    pglookout: Optional[PostgreSQLDatabaseConfigPGLookoutOptions] = None
    shared_buffers_percentage: Optional[float] = None
    work_mem: Optional[int] = None


class MySQLDatabase(Base):
    """
    An accessible Managed MySQL Database.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-databases-mysql-instance
    """

    api_endpoint = "/databases/mysql/instances/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True),
        "allow_list": Property(mutable=True, unordered=True),
        "backups": Property(derived_class=MySQLDatabaseBackup),
        "cluster_size": Property(mutable=True),
        "created": Property(is_datetime=True),
        "encrypted": Property(),
        "engine": Property(),
        "hosts": Property(),
        "port": Property(),
        "region": Property(),
        "replication_type": Property(),
        "ssl_connection": Property(),
        "status": Property(volatile=True),
        "type": Property(mutable=True),
        "fork": Property(),
        "oldest_restore_time": Property(is_datetime=True),
        "updated": Property(volatile=True, is_datetime=True),
        "updates": Property(mutable=True),
        "version": Property(),
        "engine_config": Property(
            mutable=True, json_object=MySQLDatabaseConfigOptions
        ),
    }

    @property
    def credentials(self):
        """
        Display the root username and password for an accessible Managed MySQL Database.
        The Database must have an active status to perform this command.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-databases-mysql-instance-credentials

        :returns: MappedObject containing credntials for this DB
        :rtype: MappedObject
        """

        if not hasattr(self, "_credentials"):
            resp = self._client.get(
                "{}/credentials".format(MySQLDatabase.api_endpoint), model=self
            )
            self._set("_credentials", MappedObject(**resp))

        return self._credentials

    @property
    def ssl(self):
        """
        Display the SSL CA certificate for an accessible Managed MySQL Database.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-databases-mysql-instance-ssl

        :returns: MappedObject containing SSL CA certificate for this DB
        :rtype: MappedObject
        """

        if not hasattr(self, "_ssl"):
            resp = self._client.get(
                "{}/ssl".format(MySQLDatabase.api_endpoint), model=self
            )
            self._set("_ssl", MappedObject(**resp))

        return self._ssl

    def credentials_reset(self):
        """
        Reset the root password for a Managed MySQL Database.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-databases-mysql-instance-credentials-reset

        :returns: Response from the API call to reset credentials
        :rtype: dict
        """

        self.invalidate()

        return self._client.post(
            "{}/credentials/reset".format(MySQLDatabase.api_endpoint),
            model=self,
        )

    def patch(self):
        """
        Apply security patches and updates to the underlying operating system of the Managed MySQL Database.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-databases-mysql-instance-patch

        :returns: Response from the API call to apply security patches
        :rtype: dict
        """

        self.invalidate()

        return self._client.post(
            "{}/patch".format(MySQLDatabase.api_endpoint), model=self
        )

    @deprecated(
        reason="Backups are not supported for non-legacy database clusters."
    )
    def backup_create(self, label, **kwargs):
        """
        Creates a snapshot backup of a Managed MySQL Database.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-databases-mysql-instance-backup
        """

        params = {
            "label": label,
        }
        params.update(kwargs)

        self._client.post(
            "{}/backups".format(MySQLDatabase.api_endpoint),
            model=self,
            data=params,
        )
        self.invalidate()

    def invalidate(self):
        """
        Clear out cached properties.
        """

        for attr in ["_ssl", "_credentials"]:
            if hasattr(self, attr):
                delattr(self, attr)

        Base.invalidate(self)

    def suspend(self):
        """
        Suspend a MySQL Managed Database, releasing idle resources and keeping only necessary data.

        API documentation: https://techdocs.akamai.com/linode-api/reference/suspend-databases-mysql-instance
        """
        self._client.post(
            "{}/suspend".format(MySQLDatabase.api_endpoint), model=self
        )

        return self.invalidate()

    def resume(self):
        """
        Resume a suspended MySQL Managed Database.

        API documentation: https://techdocs.akamai.com/linode-api/reference/resume-databases-mysql-instance
        """
        self._client.post(
            "{}/resume".format(MySQLDatabase.api_endpoint), model=self
        )

        return self.invalidate()


class PostgreSQLDatabase(Base):
    """
    An accessible Managed PostgreSQL Database.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-databases-postgre-sql-instance
    """

    api_endpoint = "/databases/postgresql/instances/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True),
        "allow_list": Property(mutable=True, unordered=True),
        "backups": Property(derived_class=PostgreSQLDatabaseBackup),
        "cluster_size": Property(mutable=True),
        "created": Property(is_datetime=True),
        "encrypted": Property(),
        "engine": Property(),
        "hosts": Property(),
        "port": Property(),
        "region": Property(),
        "replication_commit_type": Property(),
        "replication_type": Property(),
        "ssl_connection": Property(),
        "status": Property(volatile=True),
        "type": Property(mutable=True),
        "fork": Property(),
        "oldest_restore_time": Property(is_datetime=True),
        "updated": Property(volatile=True, is_datetime=True),
        "updates": Property(mutable=True),
        "version": Property(),
        "engine_config": Property(
            mutable=True, json_object=PostgreSQLDatabaseConfigOptions
        ),
    }

    @property
    def credentials(self):
        """
        Display the root username and password for an accessible Managed PostgreSQL Database.
        The Database must have an active status to perform this command.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-databases-postgre-sql-instance-credentials

        :returns: MappedObject containing credntials for this DB
        :rtype: MappedObject
        """

        if not hasattr(self, "_credentials"):
            resp = self._client.get(
                "{}/credentials".format(PostgreSQLDatabase.api_endpoint),
                model=self,
            )
            self._set("_credentials", MappedObject(**resp))

        return self._credentials

    @property
    def ssl(self):
        """
        Display the SSL CA certificate for an accessible Managed PostgreSQL Database.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-databases-postgresql-instance-ssl

        :returns: MappedObject containing SSL CA certificate for this DB
        :rtype: MappedObject
        """

        if not hasattr(self, "_ssl"):
            resp = self._client.get(
                "{}/ssl".format(PostgreSQLDatabase.api_endpoint), model=self
            )
            self._set("_ssl", MappedObject(**resp))

        return self._ssl

    def credentials_reset(self):
        """
        Reset the root password for a Managed PostgreSQL Database.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-databases-postgre-sql-instance-credentials-reset

        :returns: Response from the API call to reset credentials
        :rtype: dict
        """

        self.invalidate()

        return self._client.post(
            "{}/credentials/reset".format(PostgreSQLDatabase.api_endpoint),
            model=self,
        )

    def patch(self):
        """
        Apply security patches and updates to the underlying operating system of the Managed PostgreSQL Database.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-databases-postgre-sql-instance-patch

        :returns: Response from the API call to apply security patches
        :rtype: dict
        """

        self.invalidate()

        return self._client.post(
            "{}/patch".format(PostgreSQLDatabase.api_endpoint), model=self
        )

    @deprecated(
        reason="Backups are not supported for non-legacy database clusters."
    )
    def backup_create(self, label, **kwargs):
        """
        Creates a snapshot backup of a Managed PostgreSQL Database.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-databases-postgre-sql-instance-backup
        """

        params = {
            "label": label,
        }
        params.update(kwargs)

        self._client.post(
            "{}/backups".format(PostgreSQLDatabase.api_endpoint),
            model=self,
            data=params,
        )
        self.invalidate()

    def invalidate(self):
        """
        Clear out cached properties.
        """

        for attr in ["_ssl", "_credentials"]:
            if hasattr(self, attr):
                delattr(self, attr)

        Base.invalidate(self)

    def suspend(self):
        """
        Suspend a PostgreSQL Managed Database, releasing idle resources and keeping only necessary data.

        API documentation: https://techdocs.akamai.com/linode-api/reference/suspend-databases-postgre-sql-instance
        """
        self._client.post(
            "{}/suspend".format(PostgreSQLDatabase.api_endpoint), model=self
        )

        return self.invalidate()

    def resume(self):
        """
        Resume a suspended PostgreSQL Managed Database.

        API documentation: https://techdocs.akamai.com/linode-api/reference/resume-databases-postgre-sql-instance
        """
        self._client.post(
            "{}/resume".format(PostgreSQLDatabase.api_endpoint), model=self
        )

        return self.invalidate()


ENGINE_TYPE_TRANSLATION = {
    "mysql": MySQLDatabase,
    "postgresql": PostgreSQLDatabase,
}


class Database(Base):
    """
    A generic Database instance.

    Note: This class does not have a corresponding GET endpoint. For detailed information
    about the database, use the .instance() property method instead.
    """

    api_endpoint = "/databases/instances/{id}"

    properties = {
        "id": Property(),
        "label": Property(),
        "allow_list": Property(unordered=True),
        "cluster_size": Property(),
        "created": Property(),
        "encrypted": Property(),
        "engine": Property(),
        "hosts": Property(),
        "instance_uri": Property(),
        "region": Property(),
        "status": Property(),
        "type": Property(),
        "fork": Property(),
        "updated": Property(),
        "updates": Property(),
        "version": Property(),
    }

    @property
    def instance(self):
        """
        Returns the underlying database object for the corresponding database
        engine. This is useful for performing operations on generic databases.

        The following is an example of printing credentials for all databases regardless of engine::

            client = LinodeClient(TOKEN)

            databases = client.database.instances()

            for db in databases:
                print(f"{db.hosts.primary}: {db.instance.credentials.username} {db.instance.credentials.password}")
        """

        if not hasattr(self, "_instance"):
            if self.engine not in ENGINE_TYPE_TRANSLATION:
                return None

            self._set(
                "_instance",
                ENGINE_TYPE_TRANSLATION[self.engine](self._client, self.id),
            )

        return self._instance

    # Since this class doesn't have a corresponding GET endpoint, this prevents an accidental call to the nonexisting endpoint.
    def _api_get(self):
        return

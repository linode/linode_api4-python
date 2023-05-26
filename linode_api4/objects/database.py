from linode_api4.objects import Base, DerivedBase, MappedObject, Property


class DatabaseType(Base):
    """
    The type of a managed database.

    API Documentation: https://www.linode.com/docs/api/databases/#managed-database-type-view
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

    API Documentation: https://www.linode.com/docs/api/databases/#managed-database-engine-view
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

            - MySQL: https://www.linode.com/docs/api/databases/#managed-mysql-database-backup-restore
            - PostgreSQL: https://www.linode.com/docs/api/databases/#managed-postgresql-database-backup-restore
        """

        return self._client.post(
            "{}/restore".format(self.api_endpoint), model=self
        )


class MySQLDatabaseBackup(DatabaseBackup):
    """
    A backup for an accessible Managed MySQL Database.

    API Documentation: https://www.linode.com/docs/api/databases/#managed-mysql-database-backup-view
    """

    api_endpoint = "/databases/mysql/instances/{database_id}/backups/{id}"


class PostgreSQLDatabaseBackup(DatabaseBackup):
    """
    A backup for an accessible Managed PostgreSQL Database.

    API Documentation: https://www.linode.com/docs/api/databases/#managed-postgresql-database-backup-view
    """

    api_endpoint = "/databases/postgresql/instances/{database_id}/backups/{id}"


class MySQLDatabase(Base):
    """
    An accessible Managed MySQL Database.

    API Documentation: https://www.linode.com/docs/api/databases/#managed-mysql-database-view
    """

    api_endpoint = "/databases/mysql/instances/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True),
        "allow_list": Property(mutable=True),
        "backups": Property(derived_class=MySQLDatabaseBackup),
        "cluster_size": Property(),
        "created": Property(is_datetime=True),
        "encrypted": Property(),
        "engine": Property(),
        "hosts": Property(),
        "port": Property(),
        "region": Property(),
        "replication_type": Property(),
        "ssl_connection": Property(),
        "status": Property(volatile=True),
        "type": Property(),
        "updated": Property(volatile=True, is_datetime=True),
        "updates": Property(mutable=True),
        "version": Property(),
    }

    @property
    def credentials(self):
        """
        Display the root username and password for an accessible Managed MySQL Database.
        The Database must have an active status to perform this command.

        API Documentation: https://www.linode.com/docs/api/databases/#managed-mysql-database-credentials-view

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

        API Documentation: https://www.linode.com/docs/api/databases/#managed-mysql-database-ssl-certificate-view

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

        API Documentation: https://www.linode.com/docs/api/databases/#managed-mysql-database-credentials-reset

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

        API Documentation: https://www.linode.com/docs/api/databases/#managed-mysql-database-patch

        :returns: Response from the API call to apply security patches
        :rtype: dict
        """

        self.invalidate()

        return self._client.post(
            "{}/patch".format(MySQLDatabase.api_endpoint), model=self
        )

    def backup_create(self, label, **kwargs):
        """
        Creates a snapshot backup of a Managed MySQL Database.

        API Documentation: https://www.linode.com/docs/api/databases/#managed-mysql-database-backup-snapshot-create
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


class PostgreSQLDatabase(Base):
    """
    An accessible Managed PostgreSQL Database.

    API Documentation: https://www.linode.com/docs/api/databases/#managed-postgresql-database-view
    """

    api_endpoint = "/databases/postgresql/instances/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True),
        "allow_list": Property(mutable=True),
        "backups": Property(derived_class=PostgreSQLDatabaseBackup),
        "cluster_size": Property(),
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
        "type": Property(),
        "updated": Property(volatile=True, is_datetime=True),
        "updates": Property(mutable=True),
        "version": Property(),
    }

    @property
    def credentials(self):
        """
        Display the root username and password for an accessible Managed PostgreSQL Database.
        The Database must have an active status to perform this command.

        API Documentation: https://www.linode.com/docs/api/databases/#managed-postgresql-database-credentials-view

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

        API Documentation: https://www.linode.com/docs/api/databases/#managed-postgresql-database-ssl-certificate-view

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

        API Documentation: https://www.linode.com/docs/api/databases/#managed-postgresql-database-credentials-reset

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

        API Documentation: https://www.linode.com/docs/api/databases/#managed-postgresql-database-patch

        :returns: Response from the API call to apply security patches
        :rtype: dict
        """

        self.invalidate()

        return self._client.post(
            "{}/patch".format(PostgreSQLDatabase.api_endpoint), model=self
        )

    def backup_create(self, label, **kwargs):
        """
        Creates a snapshot backup of a Managed PostgreSQL Database.

        API Documentation: https://www.linode.com/docs/api/databases/#managed-postgresql-database-backup-snapshot-create
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
        "allow_list": Property(),
        "cluster_size": Property(),
        "created": Property(),
        "encrypted": Property(),
        "engine": Property(),
        "hosts": Property(),
        "instance_uri": Property(),
        "region": Property(),
        "status": Property(),
        "type": Property(),
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

from linode_api4.objects import Base, Property, MappedObject, DerivedBase, UnexpectedResponseError


class DatabaseType(Base):
    api_endpoint = '/databases/types/{id}'

    properties = {
        'deprecated': Property(filterable=True),
        'disk': Property(),
        'engines': Property(),
        'id': Property(identifier=True),
        'label': Property(),
        'memory': Property(),
        'vcpus': Property(),
    }

    def _populate(self, json):
        """
        Allows changing the name "class" in JSON to "type_class" in python
        """
        super()._populate(json)

        if 'class' in json:
            setattr(self, 'type_class', json['class'])
        else:
            setattr(self, 'type_class', None)


class DatabaseEngine(Base):
    api_endpoint = '/databases/engines/{id}'

    properties = {
        'id': Property(identifier=True),
        'engine': Property(filterable=True),
        'version': Property(filterable=True),
    }


class Database(Base):
    """
    A generic Database instance.
    """

    api_endpoint = '/databases/instances/{id}'

    properties = {
        'id': Property(),
        'label': Property(),
        'allow_list': Property(),
        'cluster_size': Property(),
        'created': Property(),
        'encrypted': Property(),
        'engine': Property(),
        'hosts': Property(),
        'instance_uri': Property(),
        'region': Property(),
        'status': Property(),
        'type': Property(),
        'updated': Property(),
        'updates': Property(),
        'version': Property(),
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

        if not hasattr(self, '_instance'):
            engine_type_translation = {
                'mysql': MySQLDatabase,
                'postgresql': PostgreSQLDatabase,
            }

            if self.engine not in engine_type_translation:
                return None

            self._set('_instance', engine_type_translation[self.engine](self._client, self.id))

        return self._instance

    def invalidate(self):
        """
        Clear out cached properties.
        """

        for attr in ['_instance']:
            if hasattr(self, attr):
                delattr(self, attr)

        Base.invalidate(self)


class MySQLDatabaseBackup(DerivedBase):
    api_endpoint = '/databases/mysql/instances/{database_id}/backups/{id}'
    derived_url_path = 'backups'
    parent_id_name = 'database_id'

    properties = {
        'created': Property(is_datetime=True),
        'id': Property(identifier=True),
        'label': Property(),
        'type': Property(),
    }

    def restore(self):
        """
        Restore a backup to a Managed MySQL Database on your Account.
        """

        return self._client.post('{}/restore'.format(MySQLDatabaseBackup.api_endpoint), model=self)


class MySQLDatabase(Base):
    api_endpoint = '/databases/mysql/instances/{id}'

    properties = {
        'id': Property(identifier=True),
        'label': Property(mutable=True, filterable=True),
        'allow_list': Property(mutable=True),
        'backups': Property(derived_class=MySQLDatabaseBackup),
        'cluster_size': Property(),
        'created': Property(is_datetime=True),
        'encrypted': Property(),
        'engine': Property(filterable=True),
        'hosts': Property(),
        'port': Property(),
        'region': Property(filterable=True),
        'replication_type': Property(),
        'ssl_connection': Property(),
        'status': Property(volatile=True, filterable=True),
        'type': Property(filterable=True),
        'updated': Property(volatile=True, is_datetime=True),
        'updates': Property(mutable=True),
        'version': Property(filterable=True),
    }

    @property
    def credentials(self):
        if not hasattr(self, '_credentials'):
            resp = self._client.get('{}/credentials'.format(MySQLDatabase.api_endpoint), model=self)
            self._set('_credentials', MappedObject(**resp))

        return self._credentials

    @property
    def ssl(self):
        if not hasattr(self, '_ssl'):
            resp = self._client.get('{}/ssl'.format(MySQLDatabase.api_endpoint), model=self)
            self._set('_ssl', MappedObject(**resp))

        return self._ssl

    def credentials_reset(self):
        """
        Reset the root password for a Managed MySQL Database.
        """

        self.invalidate()

        return self._client.post('{}/credentials/reset'.format(MySQLDatabase.api_endpoint), model=self)

    def patch(self):
        """
        Apply security patches and updates to the underlying operating system of the Managed MySQL Database.
        """

        self.invalidate()

        return self._client.post('{}/patch'.format(MySQLDatabase.api_endpoint), model=self)

    def backup_create(self, label, **kwargs):
        """
        Creates a snapshot backup of a Managed MySQL Database.
        """

        params = {
            'label': label,
        }
        params.update(kwargs)

        result = self._client.post('{}/backups'.format(MySQLDatabase.api_endpoint), model=self, data=params)
        self.invalidate()

        if 'id' not in result:
            raise UnexpectedResponseError('Unexpected response when creating backup', json=result)

        b = MySQLDatabaseBackup(self._client, result['id'], self.id, result)
        return b

    def invalidate(self):
        """
        Clear out cached properties.
        """

        for attr in ['_ssl', '_credentials']:
            if hasattr(self, attr):
                delattr(self, attr)

        Base.invalidate(self)


class PostgreSQLDatabaseBackup(DerivedBase):
    api_endpoint = '/databases/postgresql/instances/{database_id}/backups/{id}'
    derived_url_path = 'backups'
    parent_id_name = 'database_id'

    properties = {
        'created': Property(is_datetime=True),
        'id': Property(identifier=True),
        'label': Property(),
        'type': Property(),
    }

    def restore(self):
        """
        Restore a backup to a Managed PostgreSQL Database on your Account.
        """

        return self._client.post('{}/restore'.format(PostgreSQLDatabaseBackup.api_endpoint), model=self)


class PostgreSQLDatabase(Base):
    api_endpoint = '/databases/postgresql/instances/{id}'

    properties = {
        'id': Property(identifier=True),
        'label': Property(mutable=True, filterable=True),
        'allow_list': Property(mutable=True),
        'backups': Property(derived_class=PostgreSQLDatabaseBackup),
        'cluster_size': Property(),
        'created': Property(is_datetime=True),
        'encrypted': Property(),
        'engine': Property(filterable=True),
        'hosts': Property(),
        'port': Property(),
        'region': Property(filterable=True),
        'replication_commit_type': Property(),
        'replication_type': Property(),
        'ssl_connection': Property(),
        'status': Property(volatile=True, filterable=True),
        'type': Property(filterable=True),
        'updated': Property(volatile=True, is_datetime=True),
        'updates': Property(mutable=True),
        'version': Property(filterable=True),
    }

    @property
    def credentials(self):
        if not hasattr(self, '_credentials'):
            resp = self._client.get('{}/credentials'.format(PostgreSQLDatabase.api_endpoint), model=self)
            self._set('_credentials', MappedObject(**resp))

        return self._credentials

    @property
    def ssl(self):
        if not hasattr(self, '_ssl'):
            resp = self._client.get('{}/ssl'.format(PostgreSQLDatabase.api_endpoint), model=self)
            self._set('_ssl', MappedObject(**resp))

        return self._ssl

    def credentials_reset(self):
        """
        Reset the root password for a Managed PostgreSQL Database.
        """

        self.invalidate()

        return self._client.post('{}/credentials/reset'.format(PostgreSQLDatabase.api_endpoint), model=self)

    def patch(self):
        """
        Apply security patches and updates to the underlying operating system of the Managed PostgreSQL Database.
        """

        self.invalidate()

        return self._client.post('{}/patch'.format(PostgreSQLDatabase.api_endpoint), model=self)

    def backup_create(self, label, **kwargs):
        """
        Creates a snapshot backup of a Managed PostgreSQL Database.
        """

        params = {
            'label': label,
        }
        params.update(kwargs)

        result = self._client.post('{}/backups'.format(PostgreSQLDatabase.api_endpoint), model=self, data=params)
        self.invalidate()

        if 'id' not in result:
            raise UnexpectedResponseError('Unexpected response when creating backup', json=result)

        b = PostgreSQLDatabaseBackup(self._client, result['id'], self.id, result)
        return b

    def invalidate(self):
        """
        Clear out cached properties.
        """

        for attr in ['_ssl', '_credentials']:
            if hasattr(self, attr):
                delattr(self, attr)

        Base.invalidate(self)


class MongoDBDatabaseBackup(DerivedBase):
    api_endpoint = '/databases/mongodb/instances/{database_id}/backups/{id}'
    derived_url_path = 'backups'
    parent_id_name = 'database_id'

    properties = {
        'created': Property(is_datetime=True),
        'id': Property(identifier=True),
        'label': Property(),
        'type': Property(),
    }

    def restore(self):
        """
        Restore a backup to a Managed MongoDB Database on your Account.
        """

        return self._client.post('{}/restore'.format(MongoDBDatabaseBackup.api_endpoint), model=self)


class MongoDBDatabase(Base):
    api_endpoint = '/databases/mongodb/instances/{id}'

    properties = {
        'id': Property(identifier=True),
        'label': Property(mutable=True, filterable=True),
        'allow_list': Property(mutable=True),
        'backups': Property(derived_class=MongoDBDatabaseBackup),
        'cluster_size': Property(),
        'compression_type': Property(),
        'created': Property(is_datetime=True),
        'encrypted': Property(),
        'engine': Property(filterable=True),
        'hosts': Property(),
        'peers': Property(),
        'port': Property(),
        'region': Property(filterable=True),
        'replica_set': Property(),
        'ssl_connection': Property(),
        'status': Property(volatile=True, filterable=True),
        'storage_engine': Property(),
        'type': Property(filterable=True),
        'updated': Property(volatile=True, is_datetime=True),
        'updates': Property(mutable=True),
        'version': Property(filterable=True),
    }

    @property
    def credentials(self):
        if not hasattr(self, '_credentials'):
            resp = self._client.get('{}/credentials'.format(MongoDBDatabase.api_endpoint), model=self)
            self._set('_credentials', MappedObject(**resp))

        return self._credentials

    @property
    def ssl(self):
        if not hasattr(self, '_ssl'):
            resp = self._client.get('{}/ssl'.format(MongoDBDatabase.api_endpoint), model=self)
            self._set('_ssl', MappedObject(**resp))

        return self._ssl

    def credentials_reset(self):
        """
        Reset the root password for a Managed MongoDB Database.
        """

        self.invalidate()

        return self._client.post('{}/credentials/reset'.format(MongoDBDatabase.api_endpoint), model=self)

    def patch(self):
        """
        Apply security patches and updates to the underlying operating system of the Managed MongoDB Database.
        """

        self.invalidate()

        return self._client.post('{}/patch'.format(MongoDBDatabase.api_endpoint), model=self)

    def backup_create(self, label, **kwargs):
        """
        Creates a snapshot backup of a Managed MongoDB Database.
        """

        params = {
            'label': label,
        }
        params.update(kwargs)

        result = self._client.post('{}/backups'.format(MongoDBDatabase.api_endpoint), model=self, data=params)
        self.invalidate()

        if 'id' not in result:
            raise UnexpectedResponseError('Unexpected response when creating backup', json=result)

        b = MongoDBDatabaseBackup(self._client, result['id'], self.id, result)
        return b

    def invalidate(self):
        """
        Clear out cached properties.
        """

        for attr in ['_ssl', '_credentials']:
            if hasattr(self, attr):
                delattr(self, attr)

        Base.invalidate(self)

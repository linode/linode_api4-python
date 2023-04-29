



# ------- MONGODB Test cases -------
def test_get_mongodb_db_instance(get_client, test_create_mongo_db):
    dbs = get_client.database.mongodb_instances()

    for db in dbs:
        if db.id == test_create_mongo_db.id:
            database = db

    assert str(test_create_mongo_db.id) == str(database.id)
    assert str(test_create_mongo_db.label) == str(database.label)
    assert database.cluster_size == 1
    assert database.engine == "mysql"
    assert "-mysql-primary.servers.linodedb.net" in database.hosts.primary


def test_update_mongodb_db(get_client, test_create_mongo_db):
    db = get_client.load(MongoDBDatabase, test_create_mongo_db.id)

    new_allow_list = ["192.168.0.1/32"]
    label = get_test_label() + "updatedPostgresDB"

    db.allow_list = new_allow_list
    db.updates.day_of_week = 2
    db.label = label

    res = db.save()

    database = get_client.load(MongoDBDatabase, test_create_mongo_db.id)

    def get_db_status():
        return db.status == "active"

    wait_for_condition(60, 1000, get_db_status)

    assert res
    assert database.allow_list == new_allow_list
    assert database.label == label
    assert database.updates.day_of_week == 2


def test_create_mongodb_backup(get_client, test_create_mongo_db):
    db = get_client.load(MongoDBDatabase, test_create_mongo_db.id)
    label = "database_backup_test"

    def get_db_status():
        return db.status == "active"

    wait_for_condition(interval=60, timeout=1000, condition=get_db_status)

    db.backup_create(label=label, target="secondary")

    wait_for_condition(interval=60, timeout=1000, condition=get_db_status)

    # list backup and most recently created one is first element of the array
    backup = db.backups[0]

    assert backup.label == label
    assert backup.database_id == test_create_mongo_db.id


def test_mongodb_backup_restore(get_client, test_create_mongo_db):
    db = get_client.load(MongoDBDatabase, test_create_mongo_db.id)

    try:
        backup = db.backups[0]
    except IndexError as e:
        pytest.skip(
            "Skipping this test. Reason: Couldn't find db backup instance"
        )

    def get_db_restoring_status():
        return db.status == "restoring"

    backup.restore()
    wait_for_condition(
        interval=60, timeout=1000, condition=get_db_restoring_status
    )

    def get_db_active_status():
        return db.status == "active"

    wait_for_condition(
        interval=60, timeout=1000, condition=get_db_active_status
    )

    assert db.status == "active"


def test_get_mongodb_ssl(get_client, test_create_mongo_db):
    db = get_client.load(MongoDBDatabase, test_create_mongo_db.id)

    assert "ca_certificate" in str(db.ssl)


def test_mongodb_patch(get_client, test_create_mongo_db):
    db = get_client.load(MongoDBDatabase, test_create_mongo_db.id)

    db.patch()

    def get_db_status():
        return db.status == "active"

    wait_for_condition(interval=60, timeout=900, condition=get_db_status)

    assert db.status == "active"


def test_get_mongodb_credentials(get_client, test_create_mongo_db):
    db = get_client.load(MongoDBDatabase, test_create_mongo_db.id)

    assert db.credentials.username == "linroot"
    assert db.credentials.password


def test_reset_mongodb_credentials(get_client, test_create_mongo_db):
    db = get_client.load(MongoDBDatabase, test_create_mongo_db.id)

    old_pass = db.credentials.password

    db.credentials_reset()

    assert db.credentials.username == "linroot"
    assert db.credentials.password != old_pass

from test.unit.base import ClientBaseCase

from linode_api4 import PostgreSQLDatabase
from linode_api4.objects import MySQLDatabase


class MySQLDatabaseTest(ClientBaseCase):
    """
    Tests methods of the MySQLDatabase class
    """

    def test_update(self):
        """
        Test that the MySQL database can be updated
        """

        with self.mock_put("/databases/mysql/instances/123") as m:
            new_allow_list = ["192.168.0.1/32"]

            db = MySQLDatabase(self.client, 123)

            db.updates.day_of_week = 2
            db.allow_list = new_allow_list
            db.label = "cool"

            db.save()

            self.assertEqual(m.method, "put")
            self.assertEqual(m.call_url, "/databases/mysql/instances/123")
            self.assertEqual(m.call_data["label"], "cool")
            self.assertEqual(m.call_data["updates"]["day_of_week"], 2)
            self.assertEqual(m.call_data["allow_list"], new_allow_list)

    def test_list_backups(self):
        """
        Test that MySQL backups list properly
        """

        db = MySQLDatabase(self.client, 123)
        backups = db.backups

        self.assertEqual(len(backups), 1)

        self.assertEqual(backups[0].id, 456)
        self.assertEqual(
            backups[0].label, "Scheduled - 02/04/22 11:11 UTC-XcCRmI"
        )
        self.assertEqual(backups[0].type, "auto")

    def test_create_backup(self):
        """
        Test that MySQL database backups can be updated
        """

        with self.mock_post("/databases/mysql/instances/123/backups") as m:
            db = MySQLDatabase(self.client, 123)

            # We don't care about errors here; we just want to
            # validate the request.
            try:
                db.backup_create("mybackup", target="secondary")
            except Exception:
                pass

            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_url, "/databases/mysql/instances/123/backups"
            )
            self.assertEqual(m.call_data["label"], "mybackup")
            self.assertEqual(m.call_data["target"], "secondary")

    def test_backup_restore(self):
        """
        Test that MySQL database backups can be restored
        """

        with self.mock_post(
            "/databases/mysql/instances/123/backups/456/restore"
        ) as m:
            db = MySQLDatabase(self.client, 123)

            db.backups[0].restore()

            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_url, "/databases/mysql/instances/123/backups/456/restore"
            )

    def test_patch(self):
        """
        Test MySQL Database patching logic.
        """
        with self.mock_post("/databases/mysql/instances/123/patch") as m:
            db = MySQLDatabase(self.client, 123)

            db.patch()

            self.assertEqual(m.method, "post")
            self.assertEqual(m.call_url, "/databases/mysql/instances/123/patch")

    def test_get_ssl(self):
        """
        Test MySQL SSL cert logic
        """
        db = MySQLDatabase(self.client, 123)

        ssl = db.ssl

        self.assertEqual(ssl.ca_certificate, "LS0tLS1CRUdJ...==")

    def test_get_credentials(self):
        """
        Test MySQL credentials logic
        """
        db = MySQLDatabase(self.client, 123)

        creds = db.credentials

        self.assertEqual(creds.password, "s3cur3P@ssw0rd")
        self.assertEqual(creds.username, "linroot")

    def test_reset_credentials(self):
        """
        Test resetting MySQL credentials
        """
        with self.mock_post(
            "/databases/mysql/instances/123/credentials/reset"
        ) as m:
            db = MySQLDatabase(self.client, 123)

            db.credentials_reset()

            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_url, "/databases/mysql/instances/123/credentials/reset"
            )


class PostgreSQLDatabaseTest(ClientBaseCase):
    """
    Tests methods of the PostgreSQLDatabase class
    """

    def test_update(self):
        """
        Test that the PostgreSQL database can be updated
        """

        with self.mock_put("/databases/postgresql/instances/123") as m:
            new_allow_list = ["192.168.0.1/32"]

            db = PostgreSQLDatabase(self.client, 123)

            db.updates.day_of_week = 2
            db.allow_list = new_allow_list
            db.label = "cool"

            db.save()

            self.assertEqual(m.method, "put")
            self.assertEqual(m.call_url, "/databases/postgresql/instances/123")
            self.assertEqual(m.call_data["label"], "cool")
            self.assertEqual(m.call_data["updates"]["day_of_week"], 2)
            self.assertEqual(m.call_data["allow_list"], new_allow_list)

    def test_list_backups(self):
        """
        Test that PostgreSQL backups list properly
        """

        db = PostgreSQLDatabase(self.client, 123)
        backups = db.backups

        self.assertEqual(len(backups), 1)

        self.assertEqual(backups[0].id, 456)
        self.assertEqual(
            backups[0].label, "Scheduled - 02/04/22 11:11 UTC-XcCRmI"
        )
        self.assertEqual(backups[0].type, "auto")

    def test_create_backup(self):
        """
        Test that PostgreSQL database backups can be created
        """

        with self.mock_post("/databases/postgresql/instances/123/backups") as m:
            db = PostgreSQLDatabase(self.client, 123)

            # We don't care about errors here; we just want to
            # validate the request.
            try:
                db.backup_create("mybackup", target="secondary")
            except Exception:
                pass

            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_url, "/databases/postgresql/instances/123/backups"
            )
            self.assertEqual(m.call_data["label"], "mybackup")
            self.assertEqual(m.call_data["target"], "secondary")

    def test_backup_restore(self):
        """
        Test that PostgreSQL database backups can be restored
        """

        with self.mock_post(
            "/databases/postgresql/instances/123/backups/456/restore"
        ) as m:
            db = PostgreSQLDatabase(self.client, 123)

            db.backups[0].restore()

            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_url,
                "/databases/postgresql/instances/123/backups/456/restore",
            )

    def test_patch(self):
        """
        Test PostgreSQL Database patching logic.
        """
        with self.mock_post("/databases/postgresql/instances/123/patch") as m:
            db = PostgreSQLDatabase(self.client, 123)

            db.patch()

            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_url, "/databases/postgresql/instances/123/patch"
            )

    def test_get_ssl(self):
        """
        Test PostgreSQL SSL cert logic
        """
        db = PostgreSQLDatabase(self.client, 123)

        ssl = db.ssl

        self.assertEqual(ssl.ca_certificate, "LS0tLS1CRUdJ...==")

    def test_get_credentials(self):
        """
        Test PostgreSQL credentials logic
        """
        db = PostgreSQLDatabase(self.client, 123)

        creds = db.credentials

        self.assertEqual(creds.password, "s3cur3P@ssw0rd")
        self.assertEqual(creds.username, "linroot")

    def test_reset_credentials(self):
        """
        Test resetting PostgreSQL credentials
        """
        with self.mock_post(
            "/databases/postgresql/instances/123/credentials/reset"
        ) as m:
            db = PostgreSQLDatabase(self.client, 123)

            db.credentials_reset()

            self.assertEqual(m.method, "post")
            self.assertEqual(
                m.call_url,
                "/databases/postgresql/instances/123/credentials/reset",
            )

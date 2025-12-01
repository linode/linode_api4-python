from test.unit.base import ClientBaseCase

from linode_api4.objects.lock import Lock, LockEntity, LockType


class LockTest(ClientBaseCase):
    """
    Tests methods of the Lock class
    """

    def test_get_lock(self):
        """
        Tests that a lock is loaded correctly by ID
        """
        lock = Lock(self.client, 1)

        self.assertEqual(lock.id, 1)
        self.assertEqual(lock.lock_type, "cannot_delete")
        self.assertIsInstance(lock.entity, LockEntity)
        self.assertEqual(lock.entity.id, 123)
        self.assertEqual(lock.entity.type, "linode")
        self.assertEqual(lock.entity.label, "test-linode")
        self.assertEqual(lock.entity.url, "/v4/linode/instances/123")

    def test_get_locks(self):
        """
        Tests that locks can be retrieved
        """
        locks = self.client.account.locks()

        self.assertEqual(len(locks), 2)
        self.assertEqual(locks[0].id, 1)
        self.assertEqual(locks[0].lock_type, "cannot_delete")
        self.assertEqual(locks[1].id, 2)
        self.assertEqual(locks[1].lock_type, "cannot_delete_with_subresources")

    def test_create_lock(self):
        """
        Tests that a lock can be created
        """
        with self.mock_post("/locks/1") as m:
            lock = self.client.account.lock_create(
                "linode", 123, LockType.cannot_delete
            )

            self.assertEqual(m.call_url, "/locks")
            self.assertEqual(m.call_data["entity_type"], "linode")
            self.assertEqual(m.call_data["entity_id"], 123)
            self.assertEqual(m.call_data["lock_type"], "cannot_delete")

            self.assertEqual(lock.id, 1)
            self.assertEqual(lock.lock_type, "cannot_delete")

    def test_delete_lock(self):
        """
        Tests that a lock can be deleted
        """
        lock = Lock(self.client, 1)

        with self.mock_delete() as m:
            lock.delete()

            self.assertEqual(m.call_url, "/locks/1")

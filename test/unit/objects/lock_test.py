from test.unit.base import ClientBaseCase

from linode_api4.objects.lock import Lock, LockEntity


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

    def test_delete_lock(self):
        """
        Tests that a lock can be deleted using the Lock object's delete method
        """
        lock = Lock(self.client, 1)

        with self.mock_delete() as m:
            lock.delete()

            self.assertEqual(m.call_url, "/locks/1")

from test.unit.base import ClientBaseCase

from linode_api4.objects import LockType


class LockGroupTest(ClientBaseCase):
    """
    Tests methods of the LockGroup class
    """

    def test_list_locks(self):
        """
        Tests that locks can be retrieved using client.locks()
        """
        locks = self.client.locks()

        self.assertEqual(len(locks), 2)
        self.assertEqual(locks[0].id, 1)
        self.assertEqual(locks[0].lock_type, LockType.cannot_delete)
        self.assertEqual(locks[0].entity.id, 123)
        self.assertEqual(locks[0].entity.type, "linode")
        self.assertEqual(locks[1].id, 2)
        self.assertEqual(
            locks[1].lock_type, LockType.cannot_delete_with_subresources
        )
        self.assertEqual(locks[1].entity.id, 456)

    def test_create_lock(self):
        """
        Tests that a lock can be created using client.locks.create()
        """
        with self.mock_post("/locks/1") as m:
            lock = self.client.locks.create(
                entity_type="linode",
                entity_id=123,
                lock_type=LockType.cannot_delete,
            )

            self.assertEqual(m.call_url, "/locks")
            self.assertEqual(m.call_data["entity_type"], "linode")
            self.assertEqual(m.call_data["entity_id"], 123)
            self.assertEqual(m.call_data["lock_type"], LockType.cannot_delete)

            self.assertEqual(lock.id, 1)
            self.assertEqual(lock.lock_type, LockType.cannot_delete)
            self.assertIsNotNone(lock.entity)
            self.assertEqual(lock.entity.id, 123)

    def test_create_lock_with_subresources(self):
        """
        Tests that a lock with subresources can be created
        """
        with self.mock_post("/locks/1") as m:
            self.client.locks.create(
                entity_type="linode",
                entity_id=456,
                lock_type=LockType.cannot_delete_with_subresources,
            )

            self.assertEqual(m.call_url, "/locks")
            self.assertEqual(m.call_data["entity_type"], "linode")
            self.assertEqual(m.call_data["entity_id"], 456)
            self.assertEqual(
                m.call_data["lock_type"],
                LockType.cannot_delete_with_subresources,
            )

from test.integration.conftest import get_region
from test.integration.helpers import (
    get_test_label,
    send_request_when_resource_available,
)

import pytest

from linode_api4.objects import Lock, LockType


@pytest.fixture(scope="function")
def linode_for_lock(test_linode_client, e2e_test_firewall):
    """
    Create a Linode instance for testing locks.
    """
    client = test_linode_client
    region = get_region(client, {"Linodes", "Cloud Firewall"}, site_type="core")
    label = get_test_label(length=8)

    linode_instance, _ = client.linode.instance_create(
        "g6-nanode-1",
        region,
        image="linode/debian12",
        label=label,
        firewall=e2e_test_firewall,
    )

    yield linode_instance

    # Clean up any locks on the Linode before deleting it
    locks = client.locks()
    for lock in locks:
        if (
            lock.entity.id == linode_instance.id
            and lock.entity.type == "linode"
        ):
            lock.delete()

    send_request_when_resource_available(
        timeout=100, func=linode_instance.delete
    )


@pytest.fixture(scope="function")
def test_lock(test_linode_client, linode_for_lock):
    """
    Create a lock for testing.
    """
    lock = test_linode_client.locks.create(
        entity_type="linode",
        entity_id=linode_for_lock.id,
        lock_type=LockType.cannot_delete,
    )

    yield lock

    # Clean up lock if it still exists
    try:
        lock.delete()
    except Exception:
        pass  # Lock may have been deleted by the test


@pytest.mark.smoke
def test_get_lock(test_linode_client, test_lock):
    """
    Test that a lock can be retrieved by ID.
    """
    lock = test_linode_client.load(Lock, test_lock.id)

    assert lock.id == test_lock.id
    assert lock.lock_type == "cannot_delete"
    assert lock.entity is not None
    assert lock.entity.type == "linode"


def test_list_locks(test_linode_client, test_lock):
    """
    Test that locks can be listed.
    """
    locks = test_linode_client.locks()

    assert len(locks) > 0

    # Verify our test lock is in the list
    lock_ids = [lock.id for lock in locks]
    assert test_lock.id in lock_ids


def test_create_lock_cannot_delete(test_linode_client, linode_for_lock):
    """
    Test creating a cannot_delete lock.
    """
    lock = test_linode_client.locks.create(
        entity_type="linode",
        entity_id=linode_for_lock.id,
        lock_type=LockType.cannot_delete,
    )

    assert lock.id is not None
    assert lock.lock_type == "cannot_delete"
    assert lock.entity.id == linode_for_lock.id
    assert lock.entity.type == "linode"
    assert lock.entity.label == linode_for_lock.label

    # Clean up
    lock.delete()


def test_create_lock_cannot_delete_with_subresources(
    test_linode_client, linode_for_lock
):
    """
    Test creating a cannot_delete_with_subresources lock.
    """
    lock = test_linode_client.locks.create(
        entity_type="linode",
        entity_id=linode_for_lock.id,
        lock_type=LockType.cannot_delete_with_subresources,
    )

    assert lock.id is not None
    assert lock.lock_type == "cannot_delete_with_subresources"
    assert lock.entity.id == linode_for_lock.id
    assert lock.entity.type == "linode"

    # Clean up
    lock.delete()


def test_delete_lock(test_linode_client, linode_for_lock):
    """
    Test that a lock can be deleted.
    """
    # Create a lock
    lock = test_linode_client.locks.create(
        entity_type="linode",
        entity_id=linode_for_lock.id,
        lock_type=LockType.cannot_delete,
    )

    lock_id = lock.id

    # Delete the lock using the group method
    result = test_linode_client.locks.delete(lock)

    assert result is True

    # Verify the lock no longer exists
    locks = test_linode_client.locks()
    lock_ids = [l.id for l in locks]
    assert lock_id not in lock_ids


def test_delete_lock_by_id(test_linode_client, linode_for_lock):
    """
    Test that a lock can be deleted by ID.
    """
    # Create a lock
    lock = test_linode_client.locks.create(
        entity_type="linode",
        entity_id=linode_for_lock.id,
        lock_type=LockType.cannot_delete,
    )

    lock_id = lock.id

    # Delete the lock by ID
    result = test_linode_client.locks.delete(lock_id)

    assert result is True

    # Verify the lock no longer exists
    locks = test_linode_client.locks()
    lock_ids = [l.id for l in locks]
    assert lock_id not in lock_ids


def test_lock_object_delete(test_linode_client, linode_for_lock):
    """
    Test that a lock can be deleted using the Lock object's delete method.
    """
    # Create a lock
    lock = test_linode_client.locks.create(
        entity_type="linode",
        entity_id=linode_for_lock.id,
        lock_type=LockType.cannot_delete,
    )

    lock_id = lock.id

    # Delete the lock using the object method
    lock.delete()

    # Verify the lock no longer exists
    locks = test_linode_client.locks()
    lock_ids = [l.id for l in locks]
    assert lock_id not in lock_ids

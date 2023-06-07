Polling for Events
==================

There are often situations where an API request will trigger a
long-running operation (e.g. Instance shutdown) that will run
after the request has been made. These operations are tracked
through `Linode Account Events`_ which reflect the target entity,
progress, and status of these operations.

.. _Linode Account Events: https://www.linode.com/docs/api/account/#events-list

There are often cases where you would like for your application to
halt until these operations have succeeded. The most reliable and
efficient way to achieve this is by using the :py:class:`EventPoller`
object.

Polling on Basic Operations
---------------------------

In order to poll for an operation, we must create an :py:class:`EventPoller`
object *before* the endpoint that triggers the operation has been called.

Assuming a :py:class:`LinodeClient` object has already been created with the name
"client" and an :py:class:`Instance` object has already been created with the name "my_instance",
an :py:class:`EventPoller` can be created using the
:meth:`LinodeClient.polling.event_poller_create(...) <PollingGroup.event_poller_create>`
method::

    poller = client.polling.event_poller_create(
        "linode",  # The type of the target entity
        "linode_shutdown",  # The action to poll for
        entity_id=my_instance.id,  # The ID of your Linode Instance
    )

Valid values for the `type` and `action` fields can be found in the `Events Response Documentation`_.

.. _Events Response Documentation: https://www.linode.com/docs/api/account/#events-list__responses

From here, we can send the request to trigger the long-running operation::

    my_instance.shutdown()

To wait for this operation to finish, we can call the
:meth:`poller.wait_for_next_event_finished(...) <EventPoller.wait_for_next_event_finished>`
method::

    poller.wait_for_next_event_finished()

The :py:class:`timeout` and :py:class:`interval` arguments can optionally be used to configure the timeout
and poll frequency for this operation.

Bringing this together, we get the following::

    from linode_api4 import LinodeClient, Instance

    # Construct a client
    client = LinodeClient("MY_LINODE_TOKEN")

    # Fetch an existing Linode Instance
    my_instance = client.load(Instance, 12345)

    # Create the event poller
    poller = client.polling.event_poller_create(
        "linode",  # The type of the target entity
        "linode_shutdown",  # The action to poll for
        entity_id=my_instance.id,  # The ID of your Linode Instance
    )

    # Shutdown the Instance
    my_instance.shutdown()

    # Wait until the event has finished
    poller.wait_for_next_event_finished()

    print("Linode has been successfully shutdown!")

Polling for an Entity to be Free
--------------------------------

In many cases, certain operations cannot be run until any other operations running on a resource have
been completed. To ensure these operation are run reliably and do not encounter conflicts,
you can use the
:meth:`LinodeClient.polling.wait_for_entity_free(...) <PollingGroup.wait_for_entity_free>` method
to wait until a resource has no running or queued operations.

For example::

    # Construct a client
    client = LinodeClient("MY_LINODE_TOKEN")

    # Load an existing instance
    my_instance = client.load(Instance, 12345)

    # Wait until the Linode is not busy
    client.polling.wait_for_entity_free(
        "linode",
        my_instance.id
    )

    # Boot the Instance
    my_instance.boot()

The :py:class:`timeout` and :py:class:`interval` arguments can optionally be used to configure the timeout
and poll frequency for this operation.

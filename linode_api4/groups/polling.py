import polling

from linode_api4.groups import Group
from linode_api4.objects.account import Event
from linode_api4.polling import EventPoller, TimeoutContext


class PollingGroup(Group):
    """
    This group contains various helper functions for polling on Linode events.
    """

    def event_poller_create(
        self,
        entity_type: str,
        action: str,
        entity_id: int = None,
    ) -> EventPoller:
        """
        Creates a new instance of the EventPoller class.

        :param entity_type: The type of the entity to poll for events on.
                            Valid values for this field can be found here: https://www.linode.com/docs/api/account/#events-list__responses
        :type entity_type: str
        :param action: The action that caused the Event to poll for.
                       Valid values for this field can be found here: https://www.linode.com/docs/api/account/#events-list__responses
        :type action: str
        :param entity_id: The ID of the entity to poll for.
        :type entity_id: int
        :param poll_interval: The interval in seconds to wait between polls.
        :type poll_interval: int

        :returns: The new EventPoller object.
        :rtype: EventPoller
        """

        return EventPoller(
            self.client,
            entity_type,
            action,
            entity_id=entity_id,
        )

    def wait_for_entity_free(
        self,
        entity_type: str,
        entity_id: int,
        timeout: int = 240,
        interval: int = 5,
    ):
        """
        Waits for all events relevant events to not be scheduled or in-progress.

        :param entity_type: The type of the entity to poll for events on.
                            Valid values for this field can be found here: https://www.linode.com/docs/api/account/#events-list__responses
        :type entity_type: str
        :param entity_id: The ID of the entity to poll for.
        :type entity_id: int
        :param timeout: The timeout in seconds for this polling operation.
        :type timeout: int
        :param interval: The interval in seconds to wait between polls.
        :type interval: int
        """

        timeout_ctx = TimeoutContext(timeout_seconds=timeout)

        api_filter = {
            "+order": "desc",
            "+order_by": "created",
            "entity.id": entity_id,
            "entity.type": entity_type,
        }

        def poll_func():
            events = self.client.get("/account/events", filters=api_filter)[
                "data"
            ]
            return all(
                event["status"] not in ("scheduled", "started")
                for event in events
            )

        if poll_func():
            return

        polling.poll(
            poll_func,
            step=interval,
            timeout=timeout_ctx.seconds_remaining,
        )

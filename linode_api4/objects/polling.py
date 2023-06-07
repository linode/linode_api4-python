import datetime
from typing import Any, Dict, List, Optional

import polling

from linode_api4.objects import Event


class TimeoutContext:
    """
    TimeoutContext should be used by polling resources to track their provisioning time.
    """

    def __init__(self, timeout_seconds=120):
        self._start_time = datetime.datetime.now()
        self._timeout_seconds = timeout_seconds

    def start(self, start_time=datetime.datetime.now()):
        """
        Sets the timeout start time to the current time.

        :param start_time: The moment when the context started.
        :type start_time: datetime
        """
        self._start_time = start_time

    def extend(self, seconds: int):
        """
        Extends the timeout window.

        :param seconds: The number of seconds to extend the timeout period by.
        :type seconds: int
        """
        self._timeout_seconds += seconds

    @property
    def expired(self):
        """
        Whether the current timeout period has been exceeded.

        :returns: Whether this context is expired.
        :rtype: bool
        """
        return self.seconds_remaining < 0

    @property
    def valid(self):
        """
        Whether the current timeout period has not been exceeded.

        :returns: Whether this context is valid.
        :rtype: bool
        """
        return not self.expired

    @property
    def seconds_remaining(self):
        """
        The number of seconds until the timeout period has expired.

        :returns: The number of seconds remaining in this context.
        :rtype: int
        """
        return self._timeout_seconds - self.seconds_since_started

    @property
    def seconds_since_started(self):
        """
        The number of seconds since the timeout period started.

        :returns: The number of seconds since the context started.
        :rtype: int
        """
        return (datetime.datetime.now() - self._start_time).seconds


class EventPoller:
    """
    EventPoller allows modules to dynamically poll for Linode events
    """

    def __init__(
        self,
        client: "LinodeClient",
        entity_type: str,
        action: str,
        entity_id: int = None,
    ):
        self._client = client
        self._entity_type = entity_type
        self._entity_id = entity_id
        self._action = action

        # Initialize with an empty cache if no entity is specified
        if self._entity_id is None:
            self._previous_event_cache = {}
            return

        # We only want the first page of this response
        result = client.get("/account/events", filters=self._build_filter())

        self._previous_event_cache = {v["id"]: v for v in result["data"]}

    def _build_filter(self) -> Dict[str, Any]:
        """Generates a filter dict to use in HTTP requests"""
        return {
            "+order": "asc",
            "+order_by": "created",
            "entity.id": self._entity_id,
            "entity.type": self._entity_type,
            "action": self._action,
        }

    def set_entity_id(self, entity_id: int) -> None:
        """
        Sets the ID of the entity to filter on.
        This is useful for create operations where
        the entity id might not be known in __init__.

        :param entity_id: The ID of the entity to poll for.
        :type entity_id: int
        """
        self._entity_id = entity_id

    def _attempt_merge_event_into_cache(self, event: Dict[str, Any]):
        """
        Attempts to merge the given event into the event cache.
        """

        if event["id"] in self._previous_event_cache:
            return

        self._previous_event_cache[event["id"]] = event

    def _check_has_new_event(
        self, events: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        If a new event is found in the given list, return it.
        """

        for event in events:
            # Ignore cached events
            if event["id"] in self._previous_event_cache:
                continue

            return event

        return None

    def wait_for_next_event(
        self, timeout: int = 240, interval: int = 5
    ) -> Event:
        """
        Waits for and returns the next event matching the
        poller's configuration.

        :param timeout: The timeout in seconds before this polling operation will fail.
        :type timeout: int
        :param interval: The time in seconds to wait between polls.
        :type interval: int

        :returns: The resulting event.
        :rtype: Event
        """
        result_event: Dict[str, Any] = {}

        def poll_func():
            new_event = self._check_has_new_event(
                self._client.get(
                    "/account/events", filters=self._build_filter()
                )["data"]
            )

            event_exists = new_event is not None

            if event_exists:
                nonlocal result_event
                result_event = new_event
                self._attempt_merge_event_into_cache(new_event)

            return event_exists

        if poll_func():
            return Event(self._client, result_event["id"], json=result_event)

        polling.poll(
            poll_func,
            step=interval,
            timeout=timeout,
        )

        return Event(self._client, result_event["id"], json=result_event)

    def wait_for_next_event_finished(
        self, timeout: int = 240, interval: int = 5
    ) -> Event:
        """
        Waits for the next event to enter status `finished` or `notification`.

        :param timeout: The timeout in seconds before this polling operation will fail.
        :type timeout: int
        :param interval: The time in seconds to wait between polls.
        :type interval: int

        :returns: The resulting event.
        :rtype: Event
        """

        timeout_ctx = TimeoutContext(timeout_seconds=timeout)
        event = self.wait_for_next_event(timeout_ctx.seconds_remaining)

        def poll_func():
            event._api_get()
            return event.status in ["finished", "notification"]

        if poll_func():
            return event

        polling.poll(
            poll_func,
            step=interval,
            timeout=timeout_ctx.seconds_remaining,
        )

        return event

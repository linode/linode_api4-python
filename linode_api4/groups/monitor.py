__all__ = [
    "MonitorGroup",
]
from typing import Any, Optional, Union

from linode_api4 import PaginatedList
from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import (
    MonitorDashboard,
    MonitorMetricsDefinition,
    MonitorService,
    MonitorServiceToken,
    AlertDefinition,
    AlertChannel,
    RuleCriteria,
    TriggerConditions,
    AlertChannelEnvelope,
    AlertType,
    EmailChannelContent,
    ChannelContent,
)


class MonitorGroup(Group):
    """
    Encapsulates Monitor-related methods of the :any:`LinodeClient`.

    This group contains all features beneath the `/monitor` group in the API v4.
    """

    def dashboards(
        self, *filters, service_type: Optional[str] = None
    ) -> PaginatedList:
        """
        Returns a list of dashboards. If `service_type` is provided, it fetches dashboards
        for the specific service type. If None, it fetches all dashboards.

            dashboards = client.monitor.dashboards()
            dashboard = client.load(MonitorDashboard, 1)
            dashboards_by_service = client.monitor.dashboards(service_type="dbaas")

        .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.

        API Documentation:
        - All Dashboards: https://techdocs.akamai.com/linode-api/reference/get-dashboards-all
        - Dashboards by Service: https://techdocs.akamai.com/linode-api/reference/get-dashboards

        :param service_type: The service type to get dashboards for.
        :type service_type: Optional[str]
        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Dashboards.
        :rtype: PaginatedList of Dashboard
        """
        endpoint = (
            f"/monitor/services/{service_type}/dashboards"
            if service_type
            else "/monitor/dashboards"
        )

        return self.client._get_and_filter(
            MonitorDashboard,
            *filters,
            endpoint=endpoint,
        )

    def services(
        self,
        *filters,
    ) -> PaginatedList:
        """
        Lists services supported by ACLP.
            supported_services = client.monitor.services()
            service_details = client.monitor.load(MonitorService, "dbaas")

        .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-monitor-services
        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-monitor-services-for-service-type

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: Lists monitor services
        :rtype: PaginatedList of the Services
        """
        endpoint = "/monitor/services"

        return self.client._get_and_filter(
            MonitorService,
            *filters,
            endpoint=endpoint,
        )

    def metric_definitions(
        self, service_type: str, *filters
    ) -> list[MonitorMetricsDefinition]:
        """
        Returns metrics for a specific service type.

            metrics = client.monitor.list_metric_definitions(service_type="dbaas")
        .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-monitor-information

        :param service_type: The service type to get metrics for.
        :type service_type: str
        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: Returns a List of metrics for a service
        :rtype: PaginatedList of metrics
        """
        return self.client._get_and_filter(
            MonitorMetricsDefinition,
            *filters,
            endpoint=f"/monitor/services/{service_type}/metric-definitions",
        )

    def create_token(
        self, service_type: str, entity_ids: list[Any]
    ) -> MonitorServiceToken:
        """
        Returns a JWE Token for a specific service type.
            token = client.monitor.create_token(service_type="dbaas", entity_ids=[1234])

        .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-get-token

        :param service_type: The service type to create token for.
        :type service_type: str
        :param entity_ids: The list of entity IDs for which the token is valid.
        :type entity_ids: any

        :returns: Returns a token for a service
        :rtype: str
        """

        params = {"entity_ids": entity_ids}

        result = self.client.post(
            f"/monitor/services/{service_type}/token", data=params
        )

        if "token" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating token!", json=result
            )
        return MonitorServiceToken(token=result["token"])

    def alert_definitions(
        self,
        service_type: Optional[str] = None,
        alert_id: Optional[int] = None,
        *filters,
    ) -> Union[PaginatedList, AlertDefinition]:
        """
        Retrieve one or more alert definitions.

        If both ``service_type`` and ``alert_id`` are provided, a single
        :class:`AlertDefinition` is returned. If only ``service_type`` is
        provided (or neither), a :class:`PaginatedList` of
        :class:`AlertDefinition` objects is returned.

        Examples:
            alerts = client.monitor.alert_definitions()
            alerts_for_service = client.monitor.alert_definitions(service_type="dbaas")
            single = client.monitor.alert_definitions(service_type="dbaas", alert_id=1234)

        .. note:: This endpoint is in beta and requires the v4beta base URL.

        :param service_type: Optional service type to scope the query (e.g. ``"dbaas"``).
        :type service_type: Optional[str]
        :param alert_id: Optional alert definition ID. When provided, ``service_type`` must also be provided.
        :type alert_id: Optional[int]
        :param filters: Optional filter expressions to apply to a collection. See :doc:`Filtering Collections</linode_api4/objects/filtering>`.

        :returns: A single :class:`AlertDefinition` when ``alert_id`` is used,
                  otherwise a :class:`PaginatedList` of :class:`AlertDefinition`.
        :rtype: Union[AlertDefinition, PaginatedList[AlertDefinition]]
        """

        if alert_id is not None and service_type is None:
            raise ValueError(
                "service_type must be provided when alert_id is specified"
            )

        endpoint = "/monitor/alert-definitions"
        if service_type:
            endpoint = f"/monitor/services/{service_type}/alert-definitions"
            if alert_id:
                endpoint = f"{endpoint}/{alert_id}"
                # Requesting a single object
                alert_json = self.client.get(endpoint)
                return AlertDefinition(
                    self.client, alert_id, alert_json, service_type=service_type
                )

        # Requesting a list
        return self.client._get_and_filter(
            AlertDefinition, *filters, endpoint=endpoint
        )

    def alert_channels(self, *filters) -> PaginatedList:
        """
        List alert channels for the authenticated account.

        Alert channels describe notification destinations (email, webhook,
        PagerDuty, etc.) and are returned as :class:`AlertChannel` objects.

        Example:
            channels = client.monitor.alert_channels()

        .. note:: This endpoint is in beta and requires the v4beta base URL.

        :param filters: Optional filter expressions to apply to the collection. See :doc:`Filtering Collections</linode_api4/objects/filtering>`.
        :returns: A paginated list of :class:`AlertChannel` objects.
        :rtype: PaginatedList[AlertChannel]
        """
        return self.client._get_and_filter(AlertChannel, *filters)

    def create_alert_definition(
        self,
        service_type: str,
        label: str,
        severity: int,
        channel_ids: list[int],
        rule_criteria: dict = None,
        trigger_conditions: dict = None,
        entity_ids: Optional[list[str]] = None,
        description: Optional[str] = None,
    ) -> AlertDefinition:
        """
        Create a new alert definition for a service type.

        The alert definition configures when alerts are evaluated and which
        channels receive notifications.

        Example:
            new_alert = client.monitor.create_alert_definition(
                service_type="dbaas",
                label="High CPU",
                severity=2,
                channel_ids=[1,2],
            )

        .. note:: This endpoint is in beta and requires the v4beta base URL.

        :param service_type: Service type to create the alert for (e.g. ``"dbaas"``).
        :type service_type: str
        :param label: Human-readable label for the alert definition.
        :type label: str
        :param severity: Numeric severity value as expected by the API.
        :type severity: int
        :param channel_ids: List of alert channel IDs to notify when triggered.
        :type channel_ids: list[int]
        :param rule_criteria: Optional rule criteria payload for evaluation.
        :type rule_criteria: Optional[dict]
        :param trigger_conditions: Optional trigger conditions payload.
        :type trigger_conditions: Optional[dict]
        :param entity_ids: Optional list of entity IDs to scope the alert.
        :type entity_ids: Optional[list[str]]
        :param description: Optional longer description for the alert definition.
        :type description: Optional[str]

        :returns: The created :class:`AlertDefinition` as returned by the API.
        :rtype: AlertDefinition
        """
        params = {
            "label": label,
            "severity": severity,
            "channel_ids": channel_ids,
            "rule_criteria": rule_criteria,
            "trigger_conditions": trigger_conditions,
        }
        if description is not None:
            params["description"] = description
        if entity_ids is not None:
            params["entity_ids"] = entity_ids

        #API will handle check for service_type return error if missing
        result = self.client.post(
            f"/monitor/services/{service_type}/alert-definitions", data=params
        )

        if "id" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating alert definition!",
                json=result,
            )

        return AlertDefinition(self.client, result["id"], result)

    def update_alert_definition(
        self,
        service_type: str,
        alert_id: int,
        label: Optional[str] = None,
        severity: Optional[str] = None,
        description: Optional[str] = None,
        rule_criteria: Optional[RuleCriteria] = None,
        trigger_conditions: Optional[TriggerConditions] = None,
        entity_ids: Optional[list[str]] = None,
        channel_ids: Optional[list[int]] = None,
    ) -> AlertDefinition:
        """
        Update an existing alert definition.

        Only provided parameters will be updated; omitted fields are left unchanged.

        Example:
            updated = client.monitor.update_alert_definition(
                service_type="dbaas",
                alert_id=12345,
                label="Updated label",
            )

        .. note:: This endpoint is in beta and requires the v4beta base URL.

        :param service_type: Service type of the alert definition to update.
        :type service_type: str
        :param alert_id: ID of the alert definition to update.
        :type alert_id: int
        :param label: Optional new label for the alert definition.
        :type label: Optional[str]
        :param severity: Optional new severity value.
        :type severity: Optional[str]
        :param description: Optional new description.
        :type description: Optional[str]
        :param rule_criteria: Optional new rule criteria payload.
        :type rule_criteria: Optional[RuleCriteria]
        :param trigger_conditions: Optional new trigger conditions payload.
        :type trigger_conditions: Optional[TriggerConditions]
        :param entity_ids: Optional new list of entity IDs to scope the alert.
        :type entity_ids: Optional[list[str]]
        :param channel_ids: Optional new list of channel IDs to notify.
        :type channel_ids: Optional[list[int]]

        :returns: The updated :class:`AlertDefinition` returned by the API.
        :rtype: AlertDefinition
        """
        params = {}
        if label is not None:
            params["label"] = label
        if severity is not None:
            params["severity"] = severity
        if description is not None:
            params["description"] = description
        if rule_criteria is not None:
            params["rule_criteria"] = rule_criteria
        if trigger_conditions is not None:
            params["trigger_conditions"] = trigger_conditions
        if entity_ids is not None:
            params["entity_ids"] = entity_ids
        if channel_ids is not None:
            params["channel_ids"] = channel_ids
        
        #API will handle check for service_type and alert_id and return correct error if missing
        result = self.client.put(
            f"/monitor/services/{service_type}/alert-definitions/{alert_id}",
            data=params,
        )

        return AlertDefinition(self.client, result["id"], result)

    def delete_alert_definition(
        self, service_type: str, alert_id: int
    ) -> None:
        """
        Delete an alert definition by ID.

        Example:
            client.monitor.delete_alert_definition("dbaas", 12345)

        .. note:: This endpoint is in beta and requires the v4beta base URL.

        :param service_type: Service type of the alert definition to delete.
        :type service_type: str
        :param alert_id: ID of the alert definition to delete.
        :type alert_id: int

        :returns: None
        """
        self.client.delete(
            f"/monitor/services/{service_type}/alert-definitions/{alert_id}"
        )

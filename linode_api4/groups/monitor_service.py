from typing import Optional

from linode_api4 import (
    PaginatedList,
)
from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import (
    MonitorDashboard,
    MonitorMetricsDefinition,
    MonitorService,
    MonitorServiceToken,
)


class MonitorGroup(Group):
    """
    Encapsulates Monitor-related methods of the :any:`LinodeClient`.

    This group contains all features beneath the `/monitor` group in the API v4.
    """

    def dashboards(
        self, service_type: Optional[str] = None, *filters
    ) -> PaginatedList:
        """
        Returns a list of dashboards. If `service_type` is provided, it fetches dashboards
        for the specific service type. If None, it fetches all dashboards.

            dashboards = client.monitor_service.dashboards()
            dashboard = client.load(MonitorDashboard, 1)
            dashboards_by_service = client.monitor_service.dashboards(service_type="dbaas")

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
        self, service_type: Optional[str] = None, *filters
    ) -> list[MonitorService]:
        """
        Lists services supported by ACLP.
            supported_services = client.monitor_service.services()
            service_details = client.monitor_service.services(service_type="dbaas")

        .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-monitor-services
        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-monitor-services-for-service-type

        :param service_type: The service type to get details for.
        :type service_type: Optional[str]
        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: Lists monitor services by a given service_type
        :rtype: PaginatedList of the Services
        """
        endpoint = (
            f"/monitor/services/{service_type}"
            if service_type
            else "/monitor/services"
        )
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

            metrics = client.monitor_service.list_metric_definitions(service_type="dbaas")
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
        self, service_type: str, entity_ids: list
    ) -> MonitorServiceToken:
        """
        Returns a JWE Token for a specific service type.
            token = client.monitor_service.create_token(service_type="dbaas", entity_ids=[1234])

        .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-get-token

        :param service_type: The service type to create token for.
        :type service_type: str
        :param entity_ids: The list of entity IDs for which the token is valid.
        :type entity_ids: list of int

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

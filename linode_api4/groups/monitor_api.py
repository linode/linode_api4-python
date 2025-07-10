from typing import Optional

from linode_api4.groups import Group
from linode_api4.objects.monitor_api import EntityMetrics


class MetricsGroup(Group):
    """
    Encapsulates Monitor-related methods of the :any:`MonitorClient`.

    This group contains all features related to metrics in the API monitor-api.
    """
    def fetch_metrics(
        self,
        service_type: str,
        entity_ids: list,
        **kwargs,
    ) -> Optional[EntityMetrics]:
        """
        Returns metrics information for the individual entities within a specific service type.

        API documentation: https://techdocs.akamai.com/linode-api/reference/post-read-metric

        :param service_type: The service being monitored.
                            Currently, only the Managed Databases (dbaas) service type is supported.
        :type service_type: str

        :param entity_ids: The id for each individual entity from a service_type.
        :type entity_ids: list

        :param kwargs: Any other arguments accepted by the api. Please refer to the API documentation for full info.

        :returns: Service metrics requested.
        :rtype: EntityMetrics or None
        """

        params = {
            "entity_ids": entity_ids
        }

        params.update(kwargs)

        result = self.client.post(
            f"/monitor/services/{service_type}/metrics", data=params
        )

        return EntityMetrics.from_json(result)

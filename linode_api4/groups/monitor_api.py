__all__ = [
    "MetricsGroup",
]

from typing import Any, Dict, List, Optional, Union

from linode_api4 import drop_null_keys
from linode_api4.groups import Group
from linode_api4.objects.base import _flatten_request_body_recursive
from linode_api4.objects.monitor_api import EntityMetricOptions, EntityMetrics


class MetricsGroup(Group):
    """
    Encapsulates Monitor-related methods of the :any:`MonitorClient`.

    This group contains all features related to metrics in the API monitor-api.
    """

    def fetch_metrics(
        self,
        service_type: str,
        entity_ids: list,
        metrics: List[Union[EntityMetricOptions, Dict[str, Any]]],
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

        :param metrics: A list of metric objects, each specifying a metric name and its corresponding aggregation function.
        :type metrics: list of EntityMetricOptions or Dict[str, Any]

        :param kwargs: Any other arguments accepted by the api. Please refer to the API documentation for full info.

        :returns: Service metrics requested.
        :rtype: EntityMetrics or None
        """
        params = {
            "entity_ids": entity_ids,
            "metrics": metrics,
        }

        params.update(kwargs)

        result = self.client.post(
            f"/monitor/services/{service_type}/metrics",
            data=drop_null_keys(_flatten_request_body_recursive(params)),
        )

        return EntityMetrics.from_json(result)

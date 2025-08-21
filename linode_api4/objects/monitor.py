from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Literal

from linode_api4.objects.base import Base, Property
from linode_api4.objects.serializable import JSONObject


@dataclass
class Dimension(JSONObject):
    """
    A dimension of a metric.
    """

    name: str
    allowed_values: List[str]


@dataclass
class Rule:
    pass


class ServiceType(Enum):
    LINODE = "linode"
    DBAAS = "dbaas"


class DashboardType(Enum):
    OVERVIEW = "overview"
    DETAIL = "detail"


class MetricType(Enum):
    GAUGE = "gauge"
    COUNTER = "counter"


class MetricUnit(Enum):
    PERCENT = "%"
    BYTES = "bytes"
    BITS_PER_SECOND = "bps"
    REQUESTS_PER_SECOND = "rps"


class ChartType(Enum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"


class AggregateFunction(Enum):
    AVG = "avg"
    SUM = "sum"
    MIN = "min"
    MAX = "max"
    COUNT = "count"


@dataclass
class AlertDefinition(Base):
    """
    An alert definition for a monitor service.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-alert-definition
    """

    id: int
    label: str
    severity: str
    type: str
    description: Optional[str] = None
    conditions: Optional[list] = None
    notification_groups: Optional[list[int]] = None
    service_type: Optional[str] = None
    status: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None

    def __init__(self, client, id, json=None):
        super().__init__(client, id, json)

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        self._type = value

    def _populate(self, json):
        """
        Populates this object with data from a JSON dictionary.
        """
        for key, value in json.items():
            setattr(self, key, value)


@dataclass
class DashboardWidget(JSONObject):
    """
    A widget on a dashboard.
    """

    label: str
    metric: str
    unit: MetricUnit = ""
    data: Optional[dict] = None
    chart_type: ChartType = ""
    order: Optional[int] = None
    aggregate_function: AggregateFunction = ""
    dimensions: Optional[List[Dimension]] = None


@dataclass
class RuleCriteria:
    pass


@dataclass
class TriggerConditions:
    criteria_condition: Literal["ALL", "ANY"]
    evaluation_period_seconds: int
    polling_interval_seconds: int
    trigger_occurrences: int


@dataclass
class AlertChannel:
    id: int
    label: str
    type: str
    url: str


@dataclass
class MonitorMetricsDefinition(JSONObject):
    """
    Represents a single metric definition in the metrics definition list.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-monitor-information
    """

    metric: str = ""
    label: str = ""
    metric_type: MetricType = ""
    unit: MetricUnit = ""
    scrape_interval: int = 0
    is_alertable: bool = False
    dimensions: Optional[List[Dimension]] = None
    available_aggregate_functions: List[AggregateFunction] = field(
        default_factory=list
    )


class MonitorDashboard(Base):
    """
    Dashboard details.

    List dashboards: https://techdocs.akamai.com/linode-api/get-dashboards-all
    """

    api_endpoint = "/monitor/dashboards/{id}"
    properties = {
        "id": Property(identifier=True),
        "created": Property(is_datetime=True),
        "label": Property(),
        "service_type": Property(ServiceType),
        "type": Property(DashboardType),
        "widgets": Property(List[DashboardWidget]),
        "updated": Property(is_datetime=True),
    }


class MonitorService(Base):
    """
    Represents a single service type.
    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-monitor-services

    """

    api_endpoint = "/monitor/services/{service_type}"
    id_attribute = "service_type"
    properties = {
        "service_type": Property(ServiceType),
        "label": Property(),
    }


@dataclass
class MonitorServiceToken(JSONObject):
    """
    A token for the requested service_type.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/post-get-token
    """

    token: str = ""

class AlertType(Enum):
    CPU = "cpu"
    DISK = "disk"
    NETWORK_IN = "network_in"
    NETWORK_OUT = "network_out"
    TRANSFER = "transfer"


__all__ = [
    "ServiceType",
    "DashboardType",
    "MetricType",
    "MetricUnit",
    "ChartType",
    "AggregateFunction",
    "RuleCriteria",
    "TriggerConditions",
    "AlertChannel",
    "MonitorMetricsDefinition",
    "AlertDefinition",
    "MonitorDashboard",
    "MonitorService",
    "MonitorServiceToken",
    "AlertType",
]

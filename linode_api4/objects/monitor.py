__all__ = [
    "MonitorDashboard",
    "MonitorMetricsDefinition",
    "MonitorService",
    "MonitorServiceToken",
    "AggregateFunction",
    "RuleCriteria",
    "TriggerConditions",
    "AlertChannel",
    "AlertDefinition",
    "AlertType",
    "AlertChannelEnvelope",
    "ChannelContent",
    "EmailChannelContent",
]
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Literal, Union

from linode_api4.objects.base import Base, Property
from linode_api4.objects.serializable import JSONObject, StrEnum


class AggregateFunction(StrEnum):
    """
    Enum for supported aggregate functions.
    """

    min = "min"
    max = "max"
    avg = "avg"
    sum = "sum"
    count = "count"
    rate = "rate"
    increase = "increase"
    last = "last"


class ChartType(StrEnum):
    """
    Enum for supported chart types.
    """

    line = "line"
    area = "area"


class ServiceType(StrEnum):
    """
    Enum for supported service types.
    """

    dbaas = "dbaas"
    linode = "linode"
    lke = "lke"
    vpc = "vpc"
    nodebalancer = "nodebalancer"
    firewall = "firewall"
    object_storage = "object_storage"
    aclb = "aclb"


class MetricType(StrEnum):
    """
    Enum for supported metric type
    """

    gauge = "gauge"
    counter = "counter"
    histogram = "histogram"
    summary = "summary"


class MetricUnit(StrEnum):
    """
    Enum for supported metric units.
    """

    COUNT = "count"
    PERCENT = "percent"
    BYTE = "byte"
    SECOND = "second"
    BITS_PER_SECOND = "bits_per_second"
    MILLISECOND = "millisecond"
    KB = "KB"
    MB = "MB"
    GB = "GB"
    RATE = "rate"
    BYTES_PER_SECOND = "bytes_per_second"
    PERCENTILE = "percentile"
    RATIO = "ratio"
    OPS_PER_SECOND = "ops_per_second"
    IOPS = "iops"


class DashboardType(StrEnum):
    """
    Enum for supported dashboard types.
    """

    standard = "standard"
    custom = "custom"


@dataclass
class DashboardWidget(JSONObject):
    """
    Represents a single widget in the widgets list.
    """

    metric: str = ""
    unit: MetricUnit = ""
    label: str = ""
    color: str = ""
    size: int = 0
    chart_type: ChartType = ""
    y_label: str = ""
    aggregate_function: AggregateFunction = ""


@dataclass
class Dimension(JSONObject):
    """
    Represents a single dimension in the dimensions list.
    """

    dimension_label: Optional[str] = None
    label: Optional[str] = None
    values: Optional[List[str]] = None


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


@dataclass
class TriggerConditions(JSONObject):
    """
    Represents the trigger/evaluation configuration for an alert.

    Expected JSON example:
      "trigger_conditions": {
        "criteria_condition": "ALL",
        "evaluation_period_seconds": 60,
        "polling_interval_seconds": 10,
        "trigger_occurrences": 3
      }

    Fields:
      - criteria_condition: "ALL" or "ANY" (whether all rules must match or any)
      - evaluation_period_seconds: seconds over which the rule(s) are evaluated
      - polling_interval_seconds: how often metrics are sampled (seconds)
      - trigger_occurrences: how many consecutive evaluation periods must match to trigger
    """
    criteria_condition: Literal["ALL"] = "ALL"
    evaluation_period_seconds: int = 0
    polling_interval_seconds: int = 0
    trigger_occurrences: int = 1


@dataclass
class DimensionFilter(JSONObject):
    """
    A single dimension filter used inside a Rule.

    Example JSON:
      {
        "dimension_label": "node_type",
        "label": "Node Type",
        "operator": "eq",
        "value": "primary"
      }
    """
    dimension_label: str = ""
    label: str = ""
    operator: str = ""
    value: Union[str, int, float, bool, None] = None


@dataclass
class Rule(JSONObject):
    """
    A single rule within RuleCriteria.
    Example JSON:
      {
        "aggregate_function": "avg",
        "dimension_filters": [ ... ],
        "label": "Memory Usage",
        "metric": "memory_usage",
        "operator": "gt",
        "threshold": 95,
        "unit": "percent"
      }
    """
    aggregate_function: Union[AggregateFunction, str] = ""
    dimension_filters: Optional[List[DimensionFilter]] = field(default_factory=list)
    label: str = ""
    metric: str = ""
    operator: str = ""
    threshold: Optional[float] = None
    unit: Optional[str] = None


@dataclass
class RuleCriteria(JSONObject):
    """
    Container for a list of Rule objects, matching the JSON shape:
      "rule_criteria": { "rules": [ { ... }, ... ] }
    """
    rules: List[Rule] = field(default_factory=list)


@dataclass
class AlertChannelEnvelope(JSONObject):
    """
    Envelope for alert channel list responses.
    """
    id: int
    label: str
    type: str
    url: str


@dataclass
class AlertDefinition(Base):
    """
    An alert definition for a monitor service.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-alert-definition
    """
    id: int
    label: str
    severity: int
    _type: str
    service_type: str
    status: str
    has_more_resources: bool
    rule_criteria: list[Rule]
    trigger_conditions: TriggerConditions  
    alert_channels: list[AlertChannelEnvelope]
    created: str
    updated: str
    updated_by: str
    created_by: str
    entity_ids: list[str] = None
    description: str = None
    _class: str = None
   

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
            # Map "class" to "_class" class is a reserved word in Python
            if key == "class":  
                self._class = value
            elif hasattr(self, key):
                setattr(self, key, value)


@dataclass
class EmailChannelContent(JSONObject):
    """
    Represents the content for an email alert channel.
    """
    email_addresses: List[str] = field(default_factory=list)

@dataclass
class ChannelContent(JSONObject):
    """
    Represents the content block for an AlertChannel, which varies by channel type.
    """
    email: EmailChannelContent = None
    # Other channel types like 'webhook', 'slack' could be added here as Optional fields.

@dataclass
class AlertType(Enum):
    """
    Types of alerts that can be triggered.
    """
    SYSTEM = "system"
    USER = "user"

class AlertChannel(Base):
    """
    An alert channel through which notifications can be sent.

    This is a top-level API resource and must inherit from Base so that
    `api_list()` and pagination work correctly.
    """
    api_endpoint = "/monitor/alert-channels/{id}"
    id: int
    alerts: List[AlertChannelEnvelope]
    label: str
    channel_type: str
    content: ChannelContent
    created: str
    created_by: str
    _type: AlertType
    updated: str
    updated_by: str

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
            if hasattr(self, key):
                setattr(self, key, value)

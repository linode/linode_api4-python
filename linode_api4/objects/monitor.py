__all__ = [
       "AlertType",
    "MonitorDashboard",
    "MonitorMetricsDefinition",
    "MonitorService",
    "MonitorServiceToken",
    "AggregateFunction",
    "RuleCriteria",
    "TriggerConditions",
    "AlertChannel",
    "AlertDefinition",
    "AlertChannelEnvelope",
]
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Literal, Optional, Union

from linode_api4.objects.base import Base, Property
from linode_api4.objects import DerivedBase
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
    Represents a single alert channel entry returned inside alert definition
    responses.

    This envelope type is used when an AlertDefinition includes a list of
    alert channels. It contains lightweight information about the channel so
    that callers can display or reference the channel without performing an
    additional API lookup.

    Fields:
      - id: int - Unique identifier of the alert channel.
      - label: str - Human-readable name for the channel.
      - type: str - Channel type (e.g. 'webhook', 'email', 'pagerduty').
      - url: str - Destination URL or address associated with the channel.
    """
    id: int = 0
    label: str = ""
    type: str = ""
    url: str = ""

@dataclass
class AlertType(Enum):
    """
    Enumeration of alert origin types used by alert definitions.

    Values:
      - SYSTEM: Alerts that originate from the system (built-in or platform-managed).
      - USER: Alerts created and managed by users (custom alerts).

    The API uses this value in the `type` field of alert-definition responses.
    This enum can be used to compare or validate the `type` value when
    processing alert definitions.
    """
    SYSTEM = "system"
    USER = "user"

class AlertDefinition(DerivedBase):
    """
    Represents an alert definition for a monitor service.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-alert-definition
    """
    
    api_endpoint = "/monitor/services/{service}/alert-definitions/{id}"
    derived_url_path = "alert-definitions"
    parent_id_name =  "service"
    id_attribute = "id"

    properties = {
        "id": Property(identifier=True),
        "label": Property(),
        "severity": Property(),
        "type": Property(AlertType),
        "service_type": Property(mutable=True),
        "status": Property(mutable=True),
        "has_more_resources": Property(mutable=True),
        "rule_criteria": Property(RuleCriteria),
        "trigger_conditions": Property(TriggerConditions),
        "alert_channels": Property(List[AlertChannelEnvelope]),
        "created": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
        "updated_by": Property(),
        "created_by": Property(),
        "entity_ids": Property(List[str]),
        "description": Property(),
        "_class": Property("class"),
    }


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
    
class AlertChannel(Base):
    """
    Represents an alert channel used to deliver notifications when alerts
    fire. Alert channels define a destination and configuration for
    notifications (for example: email lists, webhooks, PagerDuty, Slack, etc.).

    This class maps to the Monitor API's `/monitor/alert-channels` resource
    and is used by the SDK to list, load, and inspect channels.
    """

    api_endpoint = "/monitor/alert-channels/"

    properties = {
        "id": Property(identifier=True),
        "label": Property(),
        "type": Property("channel_type"),
        "channel_type": Property(),
        "content": Property(ChannelContent),
        "created": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
        "created_by": Property(),
        "updated_by": Property(),
        "url": Property(),
        # Add other fields as needed
    }

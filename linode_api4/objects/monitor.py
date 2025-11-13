from dataclasses import dataclass, field
from typing import List, Optional, Union

from linode_api4.objects import DerivedBase
from linode_api4.objects.base import Base, Property
from linode_api4.objects.serializable import JSONObject, StrEnum

__all__ = [
    "AggregateFunction",
    "Alert",
    "AlertChannel",
    "AlertDefinition",
    "AlertType",
    "Alerts",
    "MonitorDashboard",
    "MonitorMetricsDefinition",
    "MonitorService",
    "MonitorServiceToken",
    "RuleCriteria",
    "TriggerConditions",
]


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
    net_load_balancer = "netloadbalancer"


class MetricType(StrEnum):
    """
    Enum for supported metric type
    """

    gauge = "gauge"
    counter = "counter"
    histogram = "histogram"
    summary = "summary"


class CriteriaCondition(StrEnum):
    """
    Enum for supported CriteriaCondition
    Currently, only ALL is supported.
    """

    all = "ALL"


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
    KILO_BYTES_PER_SECOND = "kilo_bytes_per_second"
    SESSIONS_PER_SECOND = "sessions_per_second"
    PACKETS_PER_SECOND = "packets_per_second"
    KILO_BITS_PER_SECOND = "kilo_bits_per_second"


class DashboardType(StrEnum):
    """
    Enum for supported dashboard types.
    """

    standard = "standard"
    custom = "custom"


@dataclass
class Filter(JSONObject):
    """
    Represents a filter in the filters list of a dashboard widget.
    """

    dimension_label: str = ""
    operator: str = ""
    value: str = ""


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
    group_by: Optional[List[str]] = None
    _filters: Optional[List[Filter]] = field(
        default=None, metadata={"json_key": "filters"}
    )

    def __getattribute__(self, name):
        """Override to handle the filters attribute specifically to avoid metaclass conflict."""
        if name == "filters":
            return object.__getattribute__(self, "_filters")
        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        """Override to handle setting the filters attribute."""
        if name == "filters":
            object.__setattr__(self, "_filters", value)
        else:
            object.__setattr__(self, name, value)


@dataclass
class ServiceAlert(JSONObject):
    """
    Represents alert configuration options for a monitor service.
    """

    polling_interval_seconds: Optional[List[int]] = None
    evaluation_period_seconds: Optional[List[int]] = None
    scope: Optional[List[str]] = None


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
    available_aggregate_functions: Optional[List[AggregateFunction]] = None


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
        "widgets": Property(json_object=DashboardWidget),
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
        "alert": Property(json_object=ServiceAlert),
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
      - criteria_condition: "ALL" (currently, only "ALL" is supported)
      - evaluation_period_seconds: seconds over which the rule(s) are evaluated
      - polling_interval_seconds: how often metrics are sampled (seconds)
      - trigger_occurrences: how many consecutive evaluation periods must match to trigger
    """

    criteria_condition: CriteriaCondition = CriteriaCondition.all
    evaluation_period_seconds: int = 0
    polling_interval_seconds: int = 0
    trigger_occurrences: int = 0


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
    value: Optional[str] = None


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

    aggregate_function: Optional[Union[AggregateFunction, str]] = None
    dimension_filters: Optional[List[DimensionFilter]] = None
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

    rules: Optional[List[Rule]] = None


@dataclass
class Alert(JSONObject):
    """
    Represents an alert definition reference within an AlertChannel.

    Fields:
      - id: int - Unique identifier of the alert definition.
      - label: str - Human-readable name for the alert definition.
      - type: str - Type of the alert (e.g., 'alerts-definitions').
      - url: str - API URL for the alert definition.
    """

    id: int = 0
    label: str = ""
    _type: str = field(default="", metadata={"json_key": "type"})
    url: str = ""


@dataclass
class Alerts(JSONObject):
    """
    Represents a collection of alert definitions within an AlertChannel.

    Fields:
      - items: List[Alert] - List of alert definitions.
    """

    items: List[Alert] = field(default_factory=list)


class AlertType(StrEnum):
    """
    Enumeration of alert origin types used by alert definitions.

    Values:
      - system: Alerts that originate from the system (built-in or platform-managed).
      - user: Alerts created and managed by users (custom alerts).

    The API uses this value in the `type` field of alert-definition responses.
    This enum can be used to compare or validate the `type` value when
    processing alert definitions.
    """

    system = "system"
    user = "user"


class AlertDefinition(DerivedBase):
    """
    Represents an alert definition for a monitor service.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-alert-definition
    """

    api_endpoint = "/monitor/services/{service_type}/alert-definitions/{id}"
    derived_url_path = "alert-definitions"
    parent_id_name = "service_type"
    id_attribute = "id"

    properties = {
        "id": Property(identifier=True),
        "service_type": Property(identifier=True),
        "label": Property(mutable=True),
        "severity": Property(mutable=True),
        "type": Property(mutable=True),
        "status": Property(mutable=True),
        "has_more_resources": Property(mutable=True),
        "rule_criteria": Property(mutable=True, json_object=RuleCriteria),
        "trigger_conditions": Property(
            mutable=True, json_object=TriggerConditions
        ),
        "alert_channels": Property(mutable=True, json_object=Alerts),
        "created": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
        "updated_by": Property(),
        "created_by": Property(),
        "entity_ids": Property(mutable=True),
        "description": Property(mutable=True),
        "_class": Property("class"),
    }


@dataclass
class EmailChannelContent(JSONObject):
    """
    Represents the content for an email alert channel.
    """

    email_addresses: Optional[List[str]] = None


@dataclass
class ChannelContent(JSONObject):
    """
    Represents the content block for an AlertChannel, which varies by channel type.
    """

    email: Optional[EmailChannelContent] = None
    # Other channel types like 'webhook', 'slack' could be added here as Optional fields.


class AlertChannel(Base):
    """
    Represents an alert channel used to deliver notifications when alerts
    fire. Alert channels define a destination and configuration for
    notifications (for example: email lists, webhooks, PagerDuty, Slack, etc.).

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-alert-channels

    This class maps to the Monitor API's `/monitor/alert-channels` resource
    and is used by the SDK to list, load, and inspect channels.

    NOTE: Only read operations are supported for AlertChannel at this time.
    Create, update, and delete (CRUD) operations are not allowed.
    """

    api_endpoint = "/monitor/alert-channels/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(),
        "type": Property(),
        "channel_type": Property(),
        "alerts": Property(mutable=False, json_object=Alerts),
        "content": Property(mutable=False, json_object=ChannelContent),
        "created": Property(is_datetime=True),
        "updated": Property(is_datetime=True),
        "created_by": Property(),
        "updated_by": Property(),
    }

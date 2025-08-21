__all__ = [
    "MonitorDashboard",
    "MonitorMetricsDefinition",
    "MonitorService",
    "MonitorServiceToken",
    "AggregateFunction",
    "AlertDefinition"
]
from dataclasses import dataclass, field
from typing import List, Optional, Literal

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
class DimensionFilter:
    dimension_label: str
    label: str
    operator: str  # e.g., "eq"
    value: str

@dataclass
class Rule:
    aggregate_function: str  # e.g., "avg"
    dimension_filters: List[DimensionFilter]
    label: str
    metric: str
    operator: str  # e.g., "gt"
    threshold: float
    unit: str  # e.g., "percent"

@dataclass
class RuleCriteria:
    rules: List[Rule]

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


@dataclass
class AlertDefinition(JSONObject):
    """
    Represents a single alert definition.

    API Documentation: 
        https://techdocs.akamai.com/linode-api/reference/get-alert-definition
        https://techdocs.akamai.com/linode-api/reference/get-alert-definitions
        https://techdocs.akamai.com/linode-api/reference/get-alert-definitions-for-service-type

    """
    alert_channels: List[AlertChannel] = field(default_factory=list)
    alert_class: Optional[str] = None  # Use alert_class instead of 'class' to avoid reserved keyword
    created: str = ""
    created_by: str = ""
    description: str = ""
    entity_ids: List[str] = field(default_factory=list)
    has_more_resources: Optional[bool] = None
    id: Optional[int] = None
    label: str = ""
    rule_criteria: Optional[RuleCriteria] = None
    service_type: str = ""
    severity: Optional[int] = None
    status: str = ""
    trigger_conditions: Optional[TriggerConditions] = None
    updated: str = ""
    updated_by: str = ""

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

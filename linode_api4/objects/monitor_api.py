__all__ = [
    "EntityMetrics",
    "EntityMetricsData",
    "EntityMetricsDataResult",
    "EntityMetricsStats",
]
from dataclasses import dataclass, field
from typing import List, Optional

from linode_api4 import JSONObject


@dataclass
class EntityMetricsStats(JSONObject):
    executionTimeMsec: int = 0
    seriesFetched: str = ""


@dataclass
class EntityMetricsDataResult(JSONObject):
    metric: dict = field(default_factory=dict)
    values: list = field(default_factory=list)


@dataclass
class EntityMetricsData(JSONObject):
    result: Optional[List[EntityMetricsDataResult]] = None
    resultType: str = ""


@dataclass
class EntityMetrics(JSONObject):
    data: Optional[EntityMetricsData] = None
    isPartial: bool = False
    stats: Optional[EntityMetricsStats] = None
    status: str = ""

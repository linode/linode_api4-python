from dataclasses import dataclass
from typing import List, Optional

from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects.base import Base, JSONObject, Property
from linode_api4.objects.serializable import StrEnum


class Capability(StrEnum):
    """
    An enum class representing the capabilities that Linode offers
    across different regions and services.

    These capabilities indicate what services are available in each data center.
    """

    ACLB = "Akamai Cloud Load Balancer"
    ACLP = "Akamai Cloud Pulse"
    ACLPStreams = "Akamai Cloud Pulse Streams"
    AkamaiRAMProtection = "Akamai RAM Protection"
    Backups = "Backups"
    BareMetal = "Bare Metal"
    BlockStorage = "Block Storage"
    BlockStorageEncryption = "Block Storage Encryption"
    BlockStorageMigrations = "Block Storage Migrations"
    BlockStoragePerformanceB1 = "Block Storage Performance B1"
    BlockStoragePerformanceB1Default = "Block Storage Performance B1 Default"
    CloudFirewall = "Cloud Firewall"
    CloudFirewallRuleSet = "Cloud Firewall Rule Set"
    CloudNAT = "Cloud NAT"
    DBAAS = "Managed Databases"
    DBAASBeta = "Managed Databases Beta"
    DiskEncryption = "Disk Encryption"
    DistributedPlans = "Distributed Plans"
    EdgePlans = "Edge Plans"
    GPU = "GPU Linodes"
    KubernetesEnterprise = "Kubernetes Enterprise"
    KubernetesEnterpriseBYOVPC = "Kubernetes Enterprise BYO VPC"
    KubernetesEnterpriseDualStack = "Kubernetes Enterprise Dual Stack"
    LADiskEncryption = "LA Disk Encryption"
    LinodeInterfaces = "Linode Interfaces"
    Linodes = "Linodes"
    LKE = "Kubernetes"
    LKEControlPlaneACL = "LKE Network Access Control List (IP ACL)"
    LKEHAControlPlanes = "LKE HA Control Planes"
    MachineImages = "Machine Images"
    MaintenancePolicy = "Maintenance Policy"
    Metadata = "Metadata"
    NLB = "Network LoadBalancer"
    NodeBalancers = "NodeBalancers"
    ObjectStorage = "Object Storage"
    ObjectStorageAccessKeyRegions = "Object Storage Access Key Regions"
    ObjectStorageEndpointTypes = "Object Storage Endpoint Types"
    PlacementGroup = "Placement Group"
    PremiumPlans = "Premium Plans"
    QuadraT1UVPU = "NETINT Quadra T1U"
    SMTPEnabled = "SMTP Enabled"
    StackScripts = "StackScripts"
    SupportTicketSeverity = "Support Ticket Severity"
    Vlans = "Vlans"
    VPCs = "VPCs"
    VPCDualStack = "VPC Dual Stack"
    VPCIPv6Stack = "VPC IPv6 Stack"
    VPCIPv6LargePrefixes = "VPC IPv6 Large Prefixes"
    VPCsExtra = "VPCs Extra"


@dataclass
class RegionPlacementGroupLimits(JSONObject):
    """
    Represents the Placement Group limits for the current account
    in a specific region.
    """

    maximum_pgs_per_customer: int = 0
    maximum_linodes_per_pg: int = 0


@dataclass
class RegionMonitors(JSONObject):
    """
    Represents the monitor services available in a region.
    Lists the services in this region that support metrics and alerts
    use with Akamai Cloud Pulse (ACLP).
    """

    alerts: Optional[list[str]] = None
    metrics: Optional[list[str]] = None


class Region(Base):
    """
    A Region. Regions correspond to individual data centers, each located in a different geographical area.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-region
    """

    api_endpoint = "/regions/{id}"
    properties = {
        "id": Property(identifier=True),
        "country": Property(),
        "capabilities": Property(unordered=True),
        "status": Property(),
        "resolvers": Property(),
        "label": Property(),
        "site_type": Property(),
        "placement_group_limits": Property(
            json_object=RegionPlacementGroupLimits
        ),
        "monitors": Property(json_object=RegionMonitors),
    }

    @property
    def availability(self) -> List["RegionAvailabilityEntry"]:
        result = self._client.get(
            f"{self.api_endpoint}/availability", model=self
        )

        if result is None:
            raise UnexpectedResponseError(
                "Expected availability data, got None."
            )

        return [RegionAvailabilityEntry.from_json(v) for v in result]


@dataclass
class RegionAvailabilityEntry(JSONObject):
    """
    Represents the availability of a Linode type within a region.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-region-availability
    """

    region: Optional[str] = None
    plan: Optional[str] = None
    available: bool = False

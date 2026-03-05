from dataclasses import dataclass
from typing import List, Optional

from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects.base import Base, JSONObject, Property
from linode_api4.objects.serializable import StrEnum


class Capability(StrEnum):
    """
    An enum class that represents the capabilities that Linode offers
    across different regions and services.

    These capabilities indicate what services are available in each data center.
    """

    linodes = "Linodes"
    nodebalancers = "NodeBalancers"
    block_storage = "Block Storage"
    object_storage = "Object Storage"
    object_storage_regions = "Object Storage Access Key Regions"
    object_storage_endpoint_types = "Object Storage Endpoint Types"
    lke = "Kubernetes"
    lke_ha_controlplanes = "LKE HA Control Planes"
    lke_e = "Kubernetes Enterprise"
    firewall = "Cloud Firewall"
    gpu = "GPU Linodes"
    vlans = "Vlans"
    vpcs = "VPCs"
    vpcs_extra = "VPCs Extra"
    machine_images = "Machine Images"
    dbaas = "Managed Databases"
    dbaas_beta = "Managed Databases Beta"
    bs_migrations = "Block Storage Migrations"
    metadata = "Metadata"
    premium_plans = "Premium Plans"
    edge_plans = "Edge Plans"
    distributed_plans = "Distributed Plans"
    lke_control_plane_acl = "LKE Network Access Control List (IP ACL)"
    aclb = "Akamai Cloud Load Balancer"
    support_ticket_severity = "Support Ticket Severity"
    backups = "Backups"
    placement_group = "Placement Group"
    disk_encryption = "Disk Encryption"
    la_disk_encryption = "LA Disk Encryption"
    akamai_ram_protection = "Akamai RAM Protection"
    blockstorage_encryption = "Block Storage Encryption"
    blockstorage_perf_b1 = "Block Storage Performance B1"
    blockstorage_perf_b1_default = "Block Storage Performance B1 Default"
    aclp = "Akamai Cloud Pulse"
    aclp_logs = "Akamai Cloud Pulse Logs"
    aclp_logs_lkee = "Akamai Cloud Pulse Logs LKE-E Audit"
    aclp_logs_dc_lkee = "ACLP Logs Datacenter LKE-E"
    smtp_enabled = "SMTP Enabled"
    stackscripts = "StackScripts"
    vpu = "NETINT Quadra T1U"
    linode_interfaces = "Linode Interfaces"
    maintenance_policy = "Maintenance Policy"
    vpc_dual_stack = "VPC Dual Stack"
    vpc_ipv6_stack = "VPC IPv6 Stack"
    nlb = "Network LoadBalancer"
    natgateway = "NAT Gateway"
    lke_e_byovpc = "Kubernetes Enterprise BYO VPC"
    lke_e_stacktype = "Kubernetes Enterprise Dual Stack"
    ruleset = "Cloud Firewall Rule Set"
    prefixlists = "Cloud Firewall Prefix Lists"
    current_prefixlists = "Cloud Firewall Prefix List Current References"


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

    @property
    def vpc_availability(self) -> "RegionVPCAvailability":
        """
        Returns VPC availability data for this region.

        NOTE: IPv6 VPCs may not currently be available to all users.

        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-region-vpc-availability

        :returns: VPC availability data for this region.
        :rtype: RegionVPCAvailability
        """
        result = self._client.get(
            f"{self.api_endpoint}/vpc-availability", model=self
        )

        if result is None:
            raise UnexpectedResponseError(
                "Expected VPC availability data, got None."
            )

        return RegionVPCAvailability.from_json(result)


@dataclass
class RegionAvailabilityEntry(JSONObject):
    """
    Represents the availability of a Linode type within a region.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-region-availability
    """

    region: Optional[str] = None
    plan: Optional[str] = None
    available: bool = False


@dataclass
class RegionVPCAvailability(JSONObject):
    """
    Represents the VPC availability data for a region.

    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-regions-vpc-availability

    NOTE: IPv6 VPCs may not currently be available to all users.
    """

    region: Optional[str] = None
    available: bool = False
    available_ipv6_prefix_lengths: Optional[List[int]] = None

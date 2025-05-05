from linode_api4.objects import Base, Property


class Dashboard(Base):
    """
    List dashboards: https://techdocs.akamai.com/linode-api/get-dashboards-all
    """

    api_endpoint = "/monitor/dashboards/{id}"
    properties = {
        "id": Property(identifier=True),
        "created": Property(is_datetime=True),
        "label": Property(),
        "service_type": Property(),
        "type": Property(),
        "widgets": Property(mutable=True),
        "updated": Property(is_datetime=True),
    }


class DashboardByService(Base):
    """
    Get a dashboard: https://techdocs.akamai.com/linode-api/reference/get-dashboards
    """

    properties = {
        "id": Property(identifier=True),
        "created": Property(is_datetime=True),
        "label": Property(),
        "service_type": Property(),
        "type": Property(),
        "widgets": Property(mutable=True),
        "updated": Property(is_datetime=True),
    }


class MonitorServiceSupported(Base):

    api_endpoint = "/monitor/services/"
    id_attribute = "service_type"
    properties = {
        "service_type": Property(),
        "label": Property(mutable=True),
    }


class ServiceDetails(Base):
    """
    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-monitor-services-for-service-type
    """

    id_attribute = "service_type"
    properties = {
        "label": Property(),
        "service_type": Property(),
    }


class MetricDefinition(Base):
    """
    API Documentation: https://techdocs.akamai.com/linode-api/reference/get-monitor-information
    """

    id_attribute = "metric"
    properties = {
        "available_aggregate_functions": Property(),
        "dimensions": Property(mutable=True),
        "label": Property(),
        "is_alertable": Property(),
        "metric": Property(),
        "metric_type": Property(),
        "scrape_interval": Property(),
        "unit": Property(),
    }


class CreateToken(Base):
    """
    API Documentation: https://techdocs.akamai.com/linode-api/reference/post-get-token
    """

    properties = {"token": Property(mutable=True)}

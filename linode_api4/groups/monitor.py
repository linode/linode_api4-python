from linode_api4.errors import UnexpectedResponseError
from linode_api4.groups import Group
from linode_api4.objects import (
    CreateToken,
    Dashboard,
    DashboardByService,
    MetricDefinition,
    MonitorServiceSupported,
    ServiceDetails,
)


class MonitorGroup(Group):
    """
    Encapsulates Monitor-related methods of the :any:`LinodeClient`.  This
    should not be instantiated on its own, but should instead be used through
    an instance of :any:`LinodeClient`::

       client = LinodeClient(token)
       instances = client.monitor.dashboards() # use the LKEGroup

    This group contains all features beneath the `/monitor` group in the API v4.
    """

    def dashboards(self, *filters):
        """
        Returns a list of dashboards on your account. 

        .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.
        
        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-dashboards-all

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Dashboards.
        :rtype: PaginatedList of Dashboard
        """
        return self.client._get_and_filter(Dashboard, *filters)


    
    def dashboards_by_service(self, service_type: str, *filters):
        """
        Returns a dashboards on your account based on the service passed. 

        .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.
        
        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-dashboards

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A Dashboards filtered by Service Type.
        :rtype: PaginatedList of the Dashboards
        """
        
        return self.client._get_and_filter(
            DashboardByService,
            *filters,
            endpoint=f"/monitor/services/{service_type}/dashboards",
        )


    def supported_services(self, *filters):
        """
        Returns a list of services supported by ACLP. 

        .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.
        
        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-monitor-services

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: A list of Supported Services
        :rtype: PaginatedList of the Dashboards
        """

        return self.client._get_and_filter(MonitorServiceSupported, *filters)

    def details_by_service(self, service_type: str,*filters):
        """
        Returns a details about a particular service. 

        .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.
        
        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-monitor-services-for-service-type

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: Details about a  Supported Services
        :rtype: PaginatedList of the Service 
        """
        return self.client._get_and_filter(
            ServiceDetails,
            *filters,
            endpoint=f"/monitor/services/{service_type}",
        )
    
    def metric_definitions(self, service_type: str,*filters):
        """
        Returns metrics for a specific service type. 

        .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.
        
        API Documentation: https://techdocs.akamai.com/linode-api/reference/get-monitor-information

        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: Returns a  List of metrics for a service
        :rtype: PaginatedList of metrics 
        """
        return self.client._get_and_filter(
            MetricDefinition,
            *filters,
            endpoint=f"/monitor/services/{service_type}/metric-definitions",
        )
    
    def create_token(self, service_type: str, entity_ids: list, *filters):
        """
        Returns a JWE Token for a specific service type. 

        .. note:: This endpoint is in beta. This will only function if base_url is set to `https://api.linode.com/v4beta`.
        
        API Documentation: https://techdocs.akamai.com/linode-api/reference/post-get-token
        :param filters: Any number of filters to apply to this query.
                        See :doc:`Filtering Collections</linode_api4/objects/filtering>`
                        for more details on filtering.

        :returns: Returns a token for a service
        :rtype: str
        """

        params = {"entity_ids": entity_ids}

        result = self.client.post(f"/monitor/services/{service_type}/token", data=params)

        if "token" not in result:
            raise UnexpectedResponseError(
                "Unexpected response when creating token!", json=result
            )
        return CreateToken(self.client, result["token"], result)
    
   
      
    
    



    
   
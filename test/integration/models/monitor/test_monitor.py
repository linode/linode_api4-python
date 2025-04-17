import json

from linode_api4.objects import (
    MonitorServiceSupported,
    Dashboard,
    DashboardsByID,
    DashboardByService,
    ServiceDetails,
    MetricDefinition,
    CreateToken,
)
from linode_api4 import LinodeClient,MySQLDatabase
import re
import time
from test.integration.helpers import (
    get_test_label,
    send_request_when_resource_available,
    wait_for_condition,
)

import pytest



# List all dashboards
def test_get_all_dashboards(test_linode_client):
    client = test_linode_client
    dashboards = client.monitor.dashboards()
    assert isinstance(dashboards[0],Dashboard)

    dashboard_get = dashboards[0]
    dashboard_id = dashboard_get.id
    get_service_type = dashboard_get.service_type
    print(f"printing svc {get_service_type}")

    #Fetch Dashboard by ID
    dashboard_by_id = client.monitor.dashboard_by_ID(dashboard_id=dashboard_id)
    assert isinstance(dashboard_by_id, DashboardsByID)
    assert dashboard_by_id.id == dashboard_id

    #Fetch Dashboard by service_type
    dashboards_by_svc = client.monitor.dashboard_by_service(service_type=get_service_type)
    assert isinstance(dashboards_by_svc[0], DashboardByService)
    assert dashboards_by_svc[0].service_type == get_service_type

# List supported services   
def test_get_supported_services(test_linode_client):
    client = test_linode_client
    supported_services = client.monitor.supported_services()
    assert isinstance(supported_services[0], MonitorServiceSupported)

    get_supported_service = supported_services[0].service_type

    #Get details for a particular service
    service_details = client.monitor.details_by_service(service_type=get_supported_service)
    assert isinstance(service_details[0],ServiceDetails)
    assert service_details[0].service_type == get_supported_service

    #Get Metric definition details for that particular service
    metric_definitions = client.monitor.metric_definitions(service_type=get_supported_service)
    assert isinstance(metric_definitions[0],MetricDefinition)

# Test Helpers
def get_db_engine_id(client: LinodeClient, engine: str):
    engines = client.database.engines()
    engine_id = ""
    for e in engines:
        if e.engine == engine:
            engine_id = e.id

    return str(engine_id)

@pytest.fixture(scope="session")
def test_create_and_test_db(test_linode_client):
    client = test_linode_client
    label = get_test_label() + "-sqldb"
    region = "us-ord"
    engine_id = get_db_engine_id(client, "mysql")
    dbtype = "g6-standard-1"


    db = client.database.mysql_create(
        label=label,
        region=region,
        engine=engine_id,
        ltype=dbtype,
        cluster_size=None,
    )

    def get_db_status():
        return db.status == "active"

    # TAKES 15-30 MINUTES TO FULLY PROVISION DB
    wait_for_condition(60, 2000, get_db_status)

    yield db
    send_request_when_resource_available(300, db.delete)

def test_my_db_functionality(test_linode_client, test_create_and_test_db):
    client = test_linode_client
    assert test_create_and_test_db.status == "active"
    
    entity_id = test_create_and_test_db.id


    # create token for the particular service
    token = client.monitor.create_token(service_type="dbaas", entity_ids=[entity_id])
    assert isinstance(token, CreateToken)
    assert len(token.token) > 0, "Token should not be empty"
    assert hasattr(token, "token"), "Response object has no 'token' attribute"


    
  
   








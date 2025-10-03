import time
from test.integration.helpers import (
    get_test_label,
    send_request_when_resource_available,
    wait_for_condition,
)

import pytest

from linode_api4 import ApiError, LinodeClient
from linode_api4.objects import (
    AlertDefinition,
    MonitorDashboard,
    MonitorMetricsDefinition,
    MonitorService,
    MonitorServiceToken,
)


# List all dashboards
def test_get_all_dashboards(test_linode_client):
    client = test_linode_client
    dashboards = client.monitor.dashboards()
    assert isinstance(dashboards[0], MonitorDashboard)

    dashboard_get = dashboards[0]
    get_service_type = dashboard_get.service_type

    # Fetch Dashboard by ID
    dashboard_by_id = client.load(MonitorDashboard, 1)
    assert isinstance(dashboard_by_id, MonitorDashboard)
    assert dashboard_by_id.id == 1

    # #Fetch Dashboard by service_type
    dashboards_by_svc = client.monitor.dashboards(service_type=get_service_type)
    assert isinstance(dashboards_by_svc[0], MonitorDashboard)
    assert dashboards_by_svc[0].service_type == get_service_type


# List supported services
def test_get_supported_services(test_linode_client):
    client = test_linode_client
    supported_services = client.monitor.services()
    assert isinstance(supported_services[0], MonitorService)

    get_supported_service = supported_services[0].service_type

    # Get details for a particular service
    service_details = client.load(MonitorService, get_supported_service)
    assert isinstance(service_details, MonitorService)
    assert service_details.service_type == get_supported_service

    # Get Metric definition details for that particular service
    metric_definitions = client.monitor.metric_definitions(
        service_type=get_supported_service
    )
    assert isinstance(metric_definitions[0], MonitorMetricsDefinition)


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
    token = client.monitor.create_token(
        service_type="dbaas", entity_ids=[entity_id]
    )
    assert isinstance(token, MonitorServiceToken)
    assert len(token.token) > 0, "Token should not be empty"
    assert hasattr(token, "token"), "Response object has no 'token' attribute"


def test_integration_create_get_update_delete_alert_definition(
    test_linode_client,
):
    """E2E: create an alert definition, fetch it, update it, then delete it.

    This test attempts to be resilient: it cleans up the created definition
    in a finally block so CI doesn't leak resources.
    """
    client = test_linode_client
    service_type = "dbaas"
    label = get_test_label() + "-e2e-alert"

    rule_criteria = {
        "rules": [
            {
                "aggregate_function": "avg",
                "dimension_filters": [
                    {
                        "dimension_label": "node_type",
                        "label": "Node Type",
                        "operator": "eq",
                        "value": "primary",
                    }
                ],
                "label": "Memory Usage",
                "metric": "memory_usage",
                "operator": "gt",
                "threshold": 90,
                "unit": "percent",
            }  # <-- Close the rule dictionary here
        ]
    }
    trigger_conditions = {
        "criteria_condition": "ALL",
        "evaluation_period_seconds": 300,
        "polling_interval_seconds": 300,
        "trigger_occurrences": 1,
    }

    # Make the label unique and ensure it begins/ends with an alphanumeric char
    label = f"{label}-{int(time.time())}"
    description = "E2E alert created by SDK integration test"

    # Pick an existing alert channel to attach to the definition; skip if none
    channels = list(client.monitor.alert_channels())
    if not channels:
        pytest.skip(
            "No alert channels available on account for creating alert definitions"
        )

    created = None
    try:
        # Create the alert definition using API-compliant top-level fields
        created = client.monitor.create_alert_definition(
            service_type=service_type,
            label=label,
            severity=1,
            description=description,
            channel_ids=[channels[0].id],
            rule_criteria=rule_criteria,
            trigger_conditions=trigger_conditions,
        )

        assert created.id
        assert getattr(created, "label", None) == label

        # Wait for server-side processing to complete (status transitions)
        timeout = 120
        interval = 10
        start = time.time()
        while (
            getattr(created, "status", None) == "in progress"
            and (time.time() - start) < timeout
        ):
            time.sleep(interval)
            try:
                created = client.load(AlertDefinition, created.id, service_type)
            except Exception:
                # transient errors while polling; continue until timeout
                pass

        update_alert = client.load(AlertDefinition, created.id, service_type)
        update_alert.label = f"{label}-updated"
        update_alert.save()

        updated = client.load(AlertDefinition, update_alert.id, service_type)
        while (
            getattr(updated, "status", None) == "in progress"
            and (time.time() - start) < timeout
        ):
            time.sleep(interval)
            try:
                updated = client.load(AlertDefinition, updated.id, service_type)
            except Exception:
                # transient errors while polling; continue until timeout
                pass

        assert created.id == updated.id
        assert updated.label == f"{label}-updated"

    finally:
        if created:
            # Best-effort cleanup; allow transient errors.
            # max time alert should take to update
            try:
                delete_alert = client.load(
                    AlertDefinition, created.id, service_type
                )
                delete_alert.delete()
            except Exception:
                pass

            # confirm it's gone (if API returns 404 or raises)
            try:
                client.load(AlertDefinition, created.id, service_type)
                # If no exception, fail explicitly
                assert False, "Alert definition still retrievable after delete"
            except ApiError:
                # Expected: alert definition is deleted and API returns 404 or similar error
                pass
            except Exception:
                # Any other exception is acceptable here, as the resource should be gone
                pass

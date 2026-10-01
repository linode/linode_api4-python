import time
from test.integration.helpers import (
    get_test_label,
    send_request_when_resource_available,
    wait_for_condition,
)

import pytest

from linode_api4 import LinodeClient, PaginatedList
from linode_api4.objects import (
    AlertChannel,
    AlertDefinition,
    AlertDefinitionEntity,
    ApiError,
    MonitorDashboard,
    MonitorMetricsDefinition,
    MonitorService,
    MonitorServiceToken,
)
from linode_api4.objects.monitor import (
    AlertStatus,
    ChannelDetails,
    EmailDetails,
)


def wait_for_alert_ready(
    client: LinodeClient,
    alert_id: int,
    service_type: str,
    timeout: int = 360,
    initial_timeout: int = 1,
) -> AlertDefinition:
    """Wait for an alert definition to reach enabled status, with backoff."""
    start = time.time()
    interval = initial_timeout
    alert = client.load(AlertDefinition, alert_id, service_type)
    while (
        getattr(alert, "status", None)
        != AlertStatus.AlertDefinitionStatusEnabled
        and (time.time() - start) < timeout
    ):
        time.sleep(interval)
        interval *= 2
        try:
            alert._api_get()
        except ApiError as e:
            # transient errors while polling; continue until timeout
            if e.status != 404:
                raise
    return alert


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


def test_filter_and_group_by(test_linode_client):
    client = test_linode_client
    dashboards_by_svc = client.monitor.dashboards(service_type="linode")
    assert isinstance(dashboards_by_svc[0], MonitorDashboard)

    # Get the first dashboard for linode service type
    dashboard = dashboards_by_svc[0]
    assert dashboard.service_type == "linode"

    # Ensure the dashboard has widgets
    assert hasattr(
        dashboard, "widgets"
    ), "Dashboard should have widgets attribute"
    assert dashboard.widgets is not None, "Dashboard widgets should not be None"
    assert (
        len(dashboard.widgets) > 0
    ), "Dashboard should have at least one widget"

    # Test the first widget's group_by and filters fields
    widget = dashboard.widgets[0]

    # Test group_by field type
    group_by = widget.group_by
    assert group_by is None or isinstance(
        group_by, list
    ), "group_by should be None or list type"
    if group_by is not None:
        for item in group_by:
            assert isinstance(item, str), "group_by items should be strings"

    # Test filters field type
    filters = widget.filters
    assert filters is None or isinstance(
        filters, list
    ), "filters should be None or list type"
    if filters is not None:
        from linode_api4.objects.monitor import Filter

        for filter_item in filters:
            assert isinstance(
                filter_item, Filter
            ), "filter items should be Filter objects"
            assert hasattr(
                filter_item, "dimension_label"
            ), "Filter should have dimension_label"
            assert hasattr(
                filter_item, "operator"
            ), "Filter should have operator"
            assert hasattr(filter_item, "value"), "Filter should have value"


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


def test_get_not_supported_service(test_linode_client):
    client = test_linode_client
    with pytest.raises(RuntimeError) as err:
        client.load(MonitorService, "saas")
    assert "[404] Not found" in str(err.value)


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
            }
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

    # Get valid users to create an alert channel for the alert definition
    users = list(client.account.users())
    if len(users) == 0:
        pytest.skip("No account users available for creating alert channels")

    # Use the first user for the alert channel
    usernames = [users[0].username]

    created = None
    created_channel = None

    try:
        # Create a new alert channel for this test
        created_channel = client.monitor.channel_create(
            label=f"{get_test_label()}-channel-{int(time.time())}",
            channel_type="email",
            details=ChannelDetails(
                email=EmailDetails(
                    recipient_type="user",
                    usernames=usernames,
                )
            ),
        )
        # Create the alert definition using API-compliant top-level fields
        created = client.monitor.create_alert_definition(
            service_type=service_type,
            label=label,
            severity=1,
            description=description,
            channel_ids=[created_channel.id],
            rule_criteria=rule_criteria,
            trigger_conditions=trigger_conditions,
        )

        assert created.id
        assert getattr(created, "label", None) == label
        assert getattr(created, "entities", None) is not None
        assert isinstance(created.group_by, list)

        created = wait_for_alert_ready(client, created.id, service_type)

        updated = client.load(AlertDefinition, created.id, service_type)
        updated.label = f"{label}-updated"
        updated.save()
        assert getattr(updated, "entities", None) is not None

        updated = wait_for_alert_ready(client, updated.id, service_type)

        assert created.id == updated.id
        assert updated.label == f"{label}-updated"
        assert isinstance(updated.group_by, list)

    finally:
        if created:
            # Best-effort cleanup; allow transient errors.
            delete_alert = client.load(
                AlertDefinition, created.id, service_type
            )
            delete_alert.delete()
        if created_channel:
            # Clean up the created channel
            try:
                created_channel.delete()
            except Exception as e:
                # Log but don't fail if cleanup fails
                print(
                    f"Warning: Failed to delete channel {created_channel.id}: {e}"
                )


def test_alert_definition_entities(test_linode_client):
    """Test listing entities associated with an alert definition.

    This test first retrieves alert definitions for a service type, then lists entities for the first alert definition.
    It asserts that the returned entities have expected fields.
    """
    client = test_linode_client
    service_type = "dbaas"

    alert_definitions = client.monitor.alert_definitions(
        service_type=service_type
    )

    if len(alert_definitions) == 0:
        pytest.fail("No alert definitions available for dbaas service type")

    assert getattr(alert_definitions[0], "entities", None) is not None
    assert isinstance(alert_definitions[0].group_by, list)

    alert_def = alert_definitions[0]
    entities = client.monitor.alert_definition_entities(
        service_type, alert_def.id
    )

    assert isinstance(entities, PaginatedList)
    if len(entities) > 0:
        entity = entities[0]
        assert isinstance(entity, AlertDefinitionEntity)
        assert entity.id
        assert entity.label
        assert entity.url
        assert entity._type == service_type


def test_integration_create_get_update_delete_alert_channel(test_linode_client):
    """E2E: create an alert channel, fetch it, update it, then delete it.

    This test creates an alert channel with email details, retrieves it,
    updates it, and then deletes it. It ensures the full CRUD feature is
    working end-to-end against the actual API.
    """
    client = test_linode_client
    label = "pythonsdk-alert-channel-test"

    created_channel = None

    try:
        # Get valid users to use for the email alert channel
        users = list(client.account.users())
        if len(users) == 0:
            pytest.skip(
                "No account users available for creating alert channels"
            )

        # Use the first user, or first two if available
        usernames = [users[0].username]
        if len(users) > 1:
            usernames.append(users[1].username)

        # Create an alert channel with email details
        created_channel = client.monitor.channel_create(
            label=label,
            channel_type="email",
            details=ChannelDetails(
                email=EmailDetails(
                    recipient_type="user",
                    usernames=usernames,
                )
            ),
        )

        # Assert the created channel has expected properties
        assert isinstance(created_channel, AlertChannel)
        assert created_channel.id is not None
        assert created_channel.label == label
        assert created_channel.channel_type == "email"
        assert created_channel.details is not None

        # Fetch the channel to verify it exists
        channels = list(client.monitor.alert_channels())
        assert len(channels) > 0, "No channels found after creation"

        # Find the created channel in the list
        found_channel = None
        for ch in channels:
            if ch.id == created_channel.id:
                found_channel = ch
                break

        assert found_channel is not None, "Created channel not found in list"
        assert found_channel.label == label
        assert found_channel.channel_type == "email"

        # Update the channel label
        updated_label = f"{label}-updated"
        created_channel.label = updated_label
        result = created_channel.save()
        assert result is True, "Failed to update channel"

        # Fetch the updated channel to verify the change
        reloaded_channel = client.load(AlertChannel, created_channel.id)
        assert (
            reloaded_channel.label == updated_label
        ), "Channel label was not updated"

    finally:
        if created_channel:
            # Clean up: delete the created channel
            try:
                created_channel.delete()
            except Exception as e:
                # Log but don't fail if cleanup fails
                print(
                    f"Warning: Failed to delete channel {created_channel.id}: {e}"
                )


def test_integration_alert_channel_alerts(test_linode_client):
    """Test retrieving alerts associated with a specific alert channel.

    This test fetches alerts for an existing alert channel and verifies
    the paginated list of alert definitions is returned correctly.
    """
    client = test_linode_client

    # Get an existing alert channel to test with
    channels = list(client.monitor.alert_channels())
    if len(channels) == 0:
        pytest.skip("No alert channels available on account for testing")

    channel_id = channels[0].id

    # Test the alert_channel_alerts() method
    alerts = client.monitor.alert_channel_alerts(channel_id)

    assert isinstance(alerts, PaginatedList)

    # If there are alerts, verify their structure
    if len(alerts) > 0:
        alert = alerts[0]
        assert isinstance(alert, AlertDefinition)
        assert alert.id is not None
        assert alert.label is not None
        assert alert.service_type is not None


def test_integration_clone_alert_definition(test_linode_client):
    """E2E: create a source alert definition, clone it, then delete both."""
    client = test_linode_client
    service_type = "dbaas"
    source_label = f"{get_test_label()}-e2e-source-alert-{int(time.time())}"
    clone_label = f"{get_test_label()}-e2e-cloned-alert-{int(time.time())}"

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
            }
        ]
    }
    trigger_conditions = {
        "criteria_condition": "ALL",
        "evaluation_period_seconds": 300,
        "polling_interval_seconds": 300,
        "trigger_occurrences": 1,
    }

    # Get valid users to create an alert channel
    users = list(client.account.users())
    if len(users) == 0:
        pytest.skip("No account users available for creating alert channels")

    # Use the first user for the alert channel
    usernames = [users[0].username]

    created = None
    cloned_alert = None
    created_channel = None

    try:
        # Create a new alert channel for this test
        created_channel = client.monitor.channel_create(
            label=f"{get_test_label()}-channel-{int(time.time())}",
            channel_type="email",
            details=ChannelDetails(
                email=EmailDetails(
                    recipient_type="user",
                    usernames=usernames,
                )
            ),
        )
        channels = [created_channel]

        # Create the source alert definition
        created = client.monitor.create_alert_definition(
            service_type=service_type,
            label=source_label,
            severity=1,
            channel_ids=[channels[0].id],
            rule_criteria=rule_criteria,
            trigger_conditions=trigger_conditions,
        )

        created = wait_for_alert_ready(client, created.id, service_type)

        clone_trigger_conditions_overrides = {
            "criteria_condition": "ALL",
            "evaluation_period_seconds": 900,
            "polling_interval_seconds": 300,
            "trigger_occurrences": 3,
        }

        # Clone the alert definition, overriding the label and trigger conditions
        cloned_alert = client.monitor.clone_alert_definition(
            service_type=service_type,
            id=created.id,
            label=clone_label,
            trigger_conditions=clone_trigger_conditions_overrides,
        )

        cloned_alert = wait_for_alert_ready(
            client, cloned_alert.id, service_type
        )

        assert created.id
        assert cloned_alert.id
        assert cloned_alert.id != created.id
        assert cloned_alert.label == clone_label
        assert cloned_alert.label != created.label
        assert cloned_alert.scope == created.scope
        assert cloned_alert.rule_criteria is not None
        assert created.rule_criteria is not None
        assert cloned_alert.rule_criteria.dict == created.rule_criteria.dict
        assert created.trigger_conditions is not None
        assert cloned_alert.trigger_conditions is not None
        assert (
            cloned_alert.trigger_conditions.dict
            != created.trigger_conditions.dict
        )

    finally:
        if cloned_alert:
            delete_clone_alert = client.load(
                AlertDefinition, cloned_alert.id, service_type
            )
            delete_clone_alert.delete()

        if created:
            delete_source_alert = client.load(
                AlertDefinition, created.id, service_type
            )
            delete_source_alert.delete()

        if created_channel:
            # Clean up the created channel
            try:
                created_channel.delete()
            except Exception as e:
                # Log but don't fail if cleanup fails
                print(
                    f"Warning: Failed to delete channel {created_channel.id}: {e}"
                )

from test.integration.conftest import get_region
from test.integration.helpers import (
    get_test_label,
    send_request_when_resource_available,
)

import pytest

from linode_api4 import (
    MigratedInstance,
    MigrationType,
    PlacementGroup,
    PlacementGroupPolicy,
    PlacementGroupType,
)


@pytest.mark.smoke
def test_get_pg(test_linode_client, create_placement_group):
    """
    Tests that a Placement Group can be loaded.
    """
    pg = test_linode_client.load(PlacementGroup, create_placement_group.id)
    assert pg.id == create_placement_group.id


@pytest.mark.smoke
def test_update_pg(test_linode_client, create_placement_group):
    """
    Tests that a Placement Group can be updated successfully.
    """
    pg = create_placement_group
    new_label = create_placement_group.label + "-updated"

    pg.label = new_label
    pg.save()

    pg = test_linode_client.load(PlacementGroup, pg.id)

    assert pg.label == new_label


def test_pg_assignment(test_linode_client, create_placement_group_with_linode):
    """
    Tests that a Placement Group can be updated successfully.
    """
    pg, inst = create_placement_group_with_linode

    assert pg.members[0].linode_id == inst.id
    assert inst.placement_group.id == pg.id

    pg.unassign([inst])
    inst.invalidate()

    assert len(pg.members) == 0
    assert inst.placement_group is None

    pg.assign([inst])
    inst.invalidate()

    assert pg.members[0].linode_id == inst.id
    assert inst.placement_group.id == pg.id


def test_pg_migration(
    test_linode_client, e2e_test_firewall, create_placement_group
):
    """
    Tests that an instance can be migrated into and our of PGs successfully.
    """
    client = test_linode_client

    label_pg = get_test_label(10)

    label_instance = get_test_label(10)

    pg_outbound = client.placement.group_create(
        label_pg,
        get_region(test_linode_client, {"Placement Group"}),
        PlacementGroupType.anti_affinity_local,
        PlacementGroupPolicy.flexible,
    )

    linode = client.linode.instance_create(
        "g6-nanode-1",
        pg_outbound.region,
        label=label_instance,
        placement_group=pg_outbound,
    )

    pg_inbound = create_placement_group

    # Says it could take up to ~6 hrs for migration to fully complete
    send_request_when_resource_available(
        300,
        linode.initiate_migration,
        placement_group=pg_inbound.id,
        migration_type=MigrationType.COLD,
        region=pg_inbound.region,
    )

    pg_inbound = test_linode_client.load(PlacementGroup, pg_inbound.id)
    pg_outbound = test_linode_client.load(PlacementGroup, pg_outbound.id)

    assert pg_inbound.migrations.inbound[0] == MigratedInstance(
        linode_id=linode.id
    )
    assert pg_outbound.migrations.outbound[0] == MigratedInstance(
        linode_id=linode.id
    )

    linode.delete()
    pg_outbound.delete()

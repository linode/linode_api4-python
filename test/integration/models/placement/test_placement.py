import pytest

from linode_api4 import PlacementGroup


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

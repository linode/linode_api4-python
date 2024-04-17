from linode_api4 import PlacementGroup


def test_get_pg(test_linode_client, create_placement_group):
    """
    Tests that a Placement Group can be loaded.
    """
    pg = test_linode_client.load(PlacementGroup, create_placement_group.id)
    assert pg.id == create_placement_group.id


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


def test_pg_assignment(test_linode_client, create_placement_group):
    """
    Tests that a Placement Group can be updated successfully.
    """
    pg = create_placement_group
    new_label = create_placement_group.label + "-updated"

    pg.label = new_label
    pg.save()

    pg = test_linode_client.load(PlacementGroup, pg.id)

    assert pg.label == new_label

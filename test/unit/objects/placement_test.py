from test.unit.base import ClientBaseCase

from linode_api4 import PlacementGroupPolicy
from linode_api4.objects import (
    PlacementGroup,
    PlacementGroupMember,
    PlacementGroupType,
)


class PlacementTest(ClientBaseCase):
    """
    Tests methods of the Placement Group
    """

    def test_get_placement_group(self):
        """
        Tests that a Placement Group is loaded correctly by ID
        """

        pg = PlacementGroup(self.client, 123)
        assert not pg._populated

        self.validate_pg_123(pg)
        assert pg._populated

    def test_list_pgs(self):
        """
        Tests that you can list PGs.
        """

        pgs = self.client.placement.groups()

        self.validate_pg_123(pgs[0])
        assert pgs[0]._populated

    def test_create_pg(self):
        """
        Tests that you can create a Placement Group.
        """

        with self.mock_post("/placement/groups/123") as m:
            pg = self.client.placement.group_create(
                "test",
                "eu-west",
                PlacementGroupType.anti_affinity_local,
                PlacementGroupPolicy.strict,
            )

            assert m.call_url == "/placement/groups"

            self.assertEqual(
                m.call_data,
                {
                    "label": "test",
                    "region": "eu-west",
                    "placement_group_type": str(
                        PlacementGroupType.anti_affinity_local
                    ),
                    "placement_group_policy": PlacementGroupPolicy.strict,
                },
            )

            assert pg._populated
            self.validate_pg_123(pg)

    def test_pg_assign(self):
        """
        Tests that you can assign to a PG.
        """

        pg = PlacementGroup(self.client, 123)
        assert not pg._populated

        with self.mock_post("/placement/groups/123") as m:
            pg.assign([123], compliant_only=True)

            assert m.call_url == "/placement/groups/123/assign"

            # Ensure the PG state was populated
            assert pg._populated

            self.assertEqual(
                m.call_data,
                {"linodes": [123], "compliant_only": True},
            )

    def test_pg_unassign(self):
        """
        Tests that you can unassign from a PG.
        """

        pg = PlacementGroup(self.client, 123)
        assert not pg._populated

        with self.mock_post("/placement/groups/123") as m:
            pg.unassign([123])

            assert m.call_url == "/placement/groups/123/unassign"

            # Ensure the PG state was populated
            assert pg._populated

            self.assertEqual(
                m.call_data,
                {"linodes": [123]},
            )

    def validate_pg_123(self, pg: PlacementGroup):
        assert pg.id == 123
        assert pg.label == "test"
        assert pg.region.id == "eu-west"
        assert pg.placement_group_type == "anti_affinity:local"
        assert pg.placement_group_policy == "strict"
        assert pg.is_compliant
        assert pg.members[0] == PlacementGroupMember(
            linode_id=123, is_compliant=True
        )

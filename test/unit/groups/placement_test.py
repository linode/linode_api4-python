from test.unit.base import ClientBaseCase

from linode_api4 import PlacementGroupPolicy
from linode_api4.objects import (
    MigratedInstance,
    PlacementGroup,
    PlacementGroupMember,
    PlacementGroupType,
)


class PlacementTest(ClientBaseCase):
    """
    Tests methods of the Placement Group
    """

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
        assert pg.migrations.inbound[0] == MigratedInstance(linode_id=123)
        assert pg.migrations.outbound[0] == MigratedInstance(linode_id=456)

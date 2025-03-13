from test.unit.base import ClientBaseCase


class LKETierGroupTest(ClientBaseCase):
    """
    Tests methods under the LKETierGroup class.
    """

    def test_list_versions(self):
        """
        Tests that LKE versions can be listed for a given tier.
        """

        tiers = self.client.lke.tier("standard").versions()

        assert tiers[0].id == "1.32"
        assert tiers[1].id == "1.31"
        assert tiers[2].id == "1.30"

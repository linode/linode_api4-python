from test.unit.base import ClientBaseCase
from test.unit.objects.firewall_test import FirewallTemplatesTest


class NetworkingGroupTest(ClientBaseCase):
    """
    Tests methods under the NetworkingGroup class.
    """

    def test_get_templates(self):
        templates = self.client.networking.firewall_templates()

        assert templates[0].slug == "public"
        FirewallTemplatesTest.assert_rules(templates[0].rules)

        assert templates[1].slug == "vpc"
        FirewallTemplatesTest.assert_rules(templates[1].rules)

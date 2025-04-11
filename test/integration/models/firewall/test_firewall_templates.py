from linode_api4 import FirewallTemplate, MappedObject


def __assert_firewall_template_rules(rules: MappedObject):
    # We can't confidently say that these rules will not be changed
    # in the future, so we can just do basic assertions here.
    assert isinstance(rules.inbound_policy, str)
    assert len(rules.inbound_policy) > 0

    assert isinstance(rules.outbound_policy, str)
    assert len(rules.outbound_policy) > 0

    assert isinstance(rules.outbound, list)
    assert isinstance(rules.inbound, list)


def test_list_firewall_templates(test_linode_client):
    templates = test_linode_client.networking.firewall_templates()
    assert len(templates) > 0

    for template in templates:
        assert isinstance(template.slug, str)
        assert len(template.slug) > 0

        __assert_firewall_template_rules(template.rules)


def test_get_firewall_template(test_linode_client):
    template = test_linode_client.load(FirewallTemplate, "vpc")

    assert template.slug == "vpc"

    __assert_firewall_template_rules(template.rules)

import time
from test.integration.conftest import get_region
from test.integration.helpers import get_test_label

import pytest

from linode_api4.objects import Firewall, FirewallDevice


@pytest.fixture(scope="session")
def linode_fw(test_linode_client):
    client = test_linode_client
    region = get_region(client, {"Linodes", "Cloud Firewall"}, site_type="core")
    label = get_test_label()

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1", region, image="linode/debian12", label=label
    )

    yield linode_instance

    linode_instance.delete()


@pytest.mark.smoke
def test_get_firewall_rules(test_linode_client, test_firewall):
    firewall = test_linode_client.load(Firewall, test_firewall.id)
    rules = firewall.rules

    assert rules.inbound_policy in ["ACCEPT", "DROP"]
    assert rules.outbound_policy in ["ACCEPT", "DROP"]


@pytest.mark.smoke
def test_update_firewall_rules(test_linode_client, test_firewall):
    firewall = test_linode_client.load(Firewall, test_firewall.id)
    new_rules = {
        "inbound": [
            {
                "action": "ACCEPT",
                "addresses": {
                    "ipv4": ["0.0.0.0/0"],
                    "ipv6": ["ff00::/8"],
                },
                "description": "A really cool firewall rule.",
                "label": "really-cool-firewall-rule",
                "ports": "80",
                "protocol": "TCP",
            }
        ],
        "inbound_policy": "ACCEPT",
        "outbound": [],
        "outbound_policy": "DROP",
    }

    firewall.update_rules(new_rules)

    time.sleep(1)

    firewall = test_linode_client.load(Firewall, test_firewall.id)

    assert firewall.rules.inbound_policy == "ACCEPT"
    assert firewall.rules.outbound_policy == "DROP"


def test_get_devices(test_linode_client, linode_fw):
    linode = linode_fw

    firewalls = list(linode.firewalls())
    assert len(firewalls) > 0

    firewall = test_linode_client.load(Firewall, firewalls[0].id)

    devices = list(firewall.devices)
    assert any(d.entity.id == linode.id for d in devices)


def test_get_device(test_linode_client, linode_fw):
    linode = linode_fw

    firewalls = list(linode.firewalls())
    assert firewalls, "No firewalls found on Linode"

    firewall = test_linode_client.load(Firewall, firewalls[0].id)

    devices = list(firewall.devices)
    assert devices, "No devices found on Firewall"

    device = next((d for d in devices if d.entity.id == linode.id), None)
    assert device is not None, f"No FirewallDevice found for Linode {linode.id}"

    firewall_device = test_linode_client.load(
        FirewallDevice, device.id, firewall.id
    )

    assert firewall_device.entity.type == "linode"
    assert f"/v4/linode/instances/{linode.id}" in firewall_device.entity.url

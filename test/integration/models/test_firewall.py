import time

import pytest

from linode_api4.objects import Firewall, FirewallDevice


@pytest.fixture(scope="session")
def linode_fw(test_linode_client):
    client = test_linode_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    label = "linode_instance_fw_device"

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1", chosen_region, image="linode/debian10", label=label
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


def test_get_devices(test_linode_client, linode_fw, test_firewall):
    linode = linode_fw

    test_firewall.device_create(int(linode.id))

    firewall = test_linode_client.load(Firewall, test_firewall.id)

    assert len(firewall.devices) > 0


def test_get_device(test_linode_client, test_firewall, linode_fw):
    firewall = test_firewall

    firewall_device = test_linode_client.load(
        FirewallDevice, firewall.devices.first().id, firewall.id
    )

    assert firewall_device.entity.label == "linode_instance_fw_device"
    assert firewall_device.entity.type == "linode"
    assert "/v4/linode/instances/" in firewall_device.entity.url

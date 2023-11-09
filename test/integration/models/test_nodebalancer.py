import re

import pytest

from linode_api4 import ApiError
from linode_api4.objects import NodeBalancerConfig, NodeBalancerNode


@pytest.fixture(scope="session")
def linode_with_private_ip(test_linode_client):
    client = test_linode_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    label = "linode_with_privateip"

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1",
        chosen_region,
        image="linode/debian10",
        label=label,
        private_ip=True,
    )

    yield linode_instance

    linode_instance.delete()


@pytest.fixture(scope="session")
def create_nb_config(test_linode_client):
    client = test_linode_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    label = "nodebalancer_test"

    nb = client.nodebalancer_create(region=chosen_region, label=label)

    config = nb.config_create()

    yield config

    config.delete()
    nb.delete()


def test_get_nodebalancer_config(test_linode_client, create_nb_config):
    config = test_linode_client.load(
        NodeBalancerConfig,
        create_nb_config.id,
        create_nb_config.nodebalancer_id,
    )


@pytest.mark.smoke
def test_create_nb_node(
    test_linode_client, create_nb_config, linode_with_private_ip
):
    config = test_linode_client.load(
        NodeBalancerConfig,
        create_nb_config.id,
        create_nb_config.nodebalancer_id,
    )
    linode = linode_with_private_ip
    address = [a for a in linode.ipv4 if re.search("192.168.+", a)][0]
    node = config.node_create(
        "node_test", address + ":80", weight=50, mode="accept"
    )

    assert re.search("192.168.+:[0-9]+", node.address)
    assert "node_test" == node.label


def test_get_nb_node(test_linode_client, create_nb_config):
    node = test_linode_client.load(
        NodeBalancerNode,
        create_nb_config.nodes[0].id,
        (create_nb_config.id, create_nb_config.nodebalancer_id),
    )


def test_update_nb_node(test_linode_client, create_nb_config):
    config = test_linode_client.load(
        NodeBalancerConfig,
        create_nb_config.id,
        create_nb_config.nodebalancer_id,
    )
    node = config.nodes[0]
    node.label = "ThisNewLabel"
    node.weight = 50
    node.mode = "accept"
    node.save()

    node_updated = test_linode_client.load(
        NodeBalancerNode,
        create_nb_config.nodes[0].id,
        (create_nb_config.id, create_nb_config.nodebalancer_id),
    )

    assert "ThisNewLabel" == node_updated.label
    assert 50 == node_updated.weight
    assert "accept" == node_updated.mode


def test_delete_nb_node(test_linode_client, create_nb_config):
    config = test_linode_client.load(
        NodeBalancerConfig,
        create_nb_config.id,
        create_nb_config.nodebalancer_id,
    )
    node = config.nodes[0]

    node.delete()

    with pytest.raises(ApiError) as e:
        test_linode_client.load(
            NodeBalancerNode,
            create_nb_config.nodes[0].id,
            (create_nb_config.id, create_nb_config.nodebalancer_id),
        )
        assert "Not Found" in str(e.json)

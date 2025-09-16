import re
from test.integration.conftest import (
    get_api_ca_file,
    get_api_url,
    get_region,
    get_token,
)
from test.integration.helpers import get_test_label

import pytest

from linode_api4 import ApiError, LinodeClient, NodeBalancer
from linode_api4.objects import (
    NodeBalancerConfig,
    NodeBalancerNode,
    NodeBalancerType,
    RegionPrice,
)

TEST_REGION = get_region(
    LinodeClient(
        token=get_token(),
        base_url=get_api_url(),
        ca_path=get_api_ca_file(),
    ),
    {"Linodes", "Cloud Firewall", "NodeBalancers"},
    site_type="core",
)


@pytest.fixture(scope="session")
def linode_with_private_ip(test_linode_client, e2e_test_firewall):
    client = test_linode_client
    label = get_test_label(8)

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1",
        TEST_REGION,
        image="linode/debian12",
        label=label,
        private_ip=True,
        firewall=e2e_test_firewall,
    )

    yield linode_instance

    linode_instance.delete()


@pytest.fixture(scope="session")
def create_nb_config(test_linode_client, e2e_test_firewall):
    client = test_linode_client
    label = get_test_label(8)

    nb = client.nodebalancer_create(
        region=TEST_REGION, label=label, firewall=e2e_test_firewall.id
    )

    config = nb.config_create()

    yield config

    config.delete()
    nb.delete()


@pytest.fixture(scope="session")
def create_nb_config_with_udp(test_linode_client, e2e_test_firewall):
    client = test_linode_client
    label = get_test_label(8)

    nb = client.nodebalancer_create(
        region=TEST_REGION, label=label, firewall=e2e_test_firewall.id
    )

    config = nb.config_create(protocol="udp", udp_check_port=1234)

    yield config

    config.delete()
    nb.delete()


@pytest.fixture(scope="session")
def create_nb(test_linode_client, e2e_test_firewall):
    client = test_linode_client
    label = get_test_label(8)

    nb = client.nodebalancer_create(
        region=TEST_REGION, label=label, firewall=e2e_test_firewall.id
    )

    yield nb

    nb.delete()


def test_create_nb(test_linode_client, e2e_test_firewall):
    client = test_linode_client
    label = get_test_label(8)

    nb = client.nodebalancer_create(
        region=TEST_REGION,
        label=label,
        firewall=e2e_test_firewall.id,
        client_udp_sess_throttle=5,
    )

    assert TEST_REGION, nb.region
    assert label == nb.label
    assert 5 == nb.client_udp_sess_throttle

    nb.delete()


def test_get_nodebalancer_config(test_linode_client, create_nb_config):
    config = test_linode_client.load(
        NodeBalancerConfig,
        create_nb_config.id,
        create_nb_config.nodebalancer_id,
    )


def test_get_nb_config_with_udp(test_linode_client, create_nb_config_with_udp):
    config = test_linode_client.load(
        NodeBalancerConfig,
        create_nb_config_with_udp.id,
        create_nb_config_with_udp.nodebalancer_id,
    )

    assert "udp" == config.protocol
    assert 1234 == config.udp_check_port
    assert 16 == config.udp_session_timeout


def test_update_nb_config(test_linode_client, create_nb_config_with_udp):
    config = test_linode_client.load(
        NodeBalancerConfig,
        create_nb_config_with_udp.id,
        create_nb_config_with_udp.nodebalancer_id,
    )

    config.udp_check_port = 4321
    config.save()

    config_updated = test_linode_client.load(
        NodeBalancerConfig,
        create_nb_config_with_udp.id,
        create_nb_config_with_udp.nodebalancer_id,
    )

    assert 4321 == config_updated.udp_check_port


def test_get_nb(test_linode_client, create_nb):
    nb = test_linode_client.load(
        NodeBalancer,
        create_nb.id,
    )

    assert nb.id == create_nb.id


def test_update_nb(test_linode_client, create_nb):
    nb = test_linode_client.load(
        NodeBalancer,
        create_nb.id,
    )

    new_label = f"{nb.label}-ThisNewLabel"

    nb.label = new_label
    nb.client_udp_sess_throttle = 5
    nb.save()

    nb_updated = test_linode_client.load(
        NodeBalancer,
        create_nb.id,
    )

    assert new_label == nb_updated.label
    assert 5 == nb_updated.client_udp_sess_throttle


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


@pytest.mark.smoke
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

    new_label = f"{node.label}-ThisNewLabel"

    node.label = new_label
    node.weight = 50
    node.mode = "accept"
    node.save()

    node_updated = test_linode_client.load(
        NodeBalancerNode,
        create_nb_config.nodes[0].id,
        (create_nb_config.id, create_nb_config.nodebalancer_id),
    )

    assert new_label == node_updated.label
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


def test_nodebalancer_types(test_linode_client):
    types = test_linode_client.nodebalancers.types()

    if len(types) > 0:
        for nb_type in types:
            assert type(nb_type) is NodeBalancerType
            assert nb_type.price.monthly is None or (
                isinstance(nb_type.price.monthly, (float, int))
                and nb_type.price.monthly >= 0
            )
            if len(nb_type.region_prices) > 0:
                region_price = nb_type.region_prices[0]
                assert type(region_price) is RegionPrice
                assert region_price.monthly is None or (
                    isinstance(region_price.monthly, (float, int))
                    and region_price.monthly >= 0
                )

import ipaddress
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
    assert 2 == config.udp_session_timeout


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


def test_nb_with_backend_only(test_linode_client, create_vpc_with_subnet):
    client = test_linode_client
    vpc = create_vpc_with_subnet[0].id
    vpc_region = create_vpc_with_subnet[0].region
    subnet = create_vpc_with_subnet[1].id
    label = get_test_label(8)

    nb = client.nodebalancer_create(
        region=vpc_region, label=label, vpcs=[{"vpc_id": vpc,"subnet_id": subnet}]
    )

    assert isinstance(ipaddress.ip_address(nb.ipv4.address), ipaddress.IPv4Address)
    assert isinstance(ipaddress.ip_address(nb.ipv6), ipaddress.IPv6Address)
    assert nb.frontend_address_type == 'public'
    assert nb.frontend_vpc_subnet_id is None

    nb_get = NodeBalancer(client, nb.id)
    nb_vpcs = nb_get.vpcs()

    assert len(nb_vpcs) == 1
    assert nb_vpcs[0].purpose == 'backend'

    nb_vpc = nb_get.vpc(nb_vpcs[0].id)

    assert nb_vpc.purpose == 'backend'

    # TODO: There is no API implementation yet for /backend_vpcs and /frontend_vpcs
    # nb_backend_vpcs = nb_get.backend_vpcs()
    # assert len(nb_backend_vpcs) == 1
    # assert nb_backend_vpcs[0].purpose == 'backend'
    #
    # nb_frontend_vpcs = nb_get.frontend_vpcs()
    # assert len(nb_frontend_vpcs) == 0

    nb.delete()


def test_nb_with_frontend_ipv4_only_in_single_stack_vpc(test_linode_client, create_vpc_with_subnet_ipv4):
    client = test_linode_client
    vpc_region = create_vpc_with_subnet_ipv4[0].region
    subnet = create_vpc_with_subnet_ipv4[1].id
    label = get_test_label(8)
    ipv4_address = "10.0.0.2" # first available address

    nb = client.nodebalancer_create(
        region=vpc_region,
        label=label,
        frontend_vpcs=[{"subnet_id": subnet, "ipv4_range": "10.0.0.0/24"}],
        type="premium"
    )
    assert nb.ipv4.address == ipv4_address
    assert nb.ipv6 is None
    assert nb.frontend_address_type == 'vpc'
    assert nb.frontend_vpc_subnet_id == subnet

    # TODO: There is no API implementation yet for /backend_vpcs and /frontend_vpcs
    # nb_frontend_vpcs = nb_get.frontend_vpcs()
    # assert len(nb_frontend_vpcs) == 1
    # assert nb_frontend_vpcs[0].purpose == 'frontend'
    #
    # nb_backend_vpcs = nb_get.backend_vpcs()
    # assert len(nb_backend_vpcs) == 0

    nb.delete()


def test_nb_with_frontend_ipv6_only_in_single_stack_vpc(test_linode_client, create_vpc_with_subnet_ipv4):
    client = test_linode_client
    vpc_region = create_vpc_with_subnet_ipv4[0].region
    subnet = create_vpc_with_subnet_ipv4[1].id
    label = get_test_label(8)

    with pytest.raises(ApiError) as err:
        client.nodebalancer_create(
            region=vpc_region,
            label=label,
            frontend_vpcs=[{"subnet_id": subnet, "ipv6_range": "/62"}],
            type="premium"
        )
        assert "No IPv6 subnets available in VPC" in str(err.json)


def test_nb_with_frontend_and_default_type(test_linode_client, create_vpc_with_subnet):
    client = test_linode_client
    vpc_region = create_vpc_with_subnet[0].region
    subnet = create_vpc_with_subnet[1].id
    label = get_test_label(8)

    with pytest.raises(ApiError) as err:
        client.nodebalancer_create(
            region=vpc_region,
            label=label,
            frontend_vpcs=[{"subnet_id": subnet}],
        )
        assert "Nodebalancer with frontend VPC IP must be premium" in str(err.json)


def test_nb_with_frontend_and_premium40gb_type(test_linode_client):
    region = "us-iad"  # premium_40gb type can be used in specific regions only
    client = test_linode_client

    vpc = client.vpcs.create(
        label=get_test_label(length=10),
        region=region,
        description="test description",
        ipv6=[{"range": "auto"}],
    )

    subnet = vpc.subnet_create(
        label="test-subnet",
        ipv4="10.0.0.0/24",
        ipv6=[{"range": "auto"}],
    )

    nb = client.nodebalancer_create(
        region=region,
        label=get_test_label(length=8),
        frontend_vpcs=[{"subnet_id": subnet.id}],
        type="premium_40gb"
    )
    assert nb.type == 'premium_40gb'

    nb_get = test_linode_client.load(
        NodeBalancer,
        nb.id,
    )
    assert nb_get.type == 'premium_40gb'

    nb.delete()
    vpc.delete()


def test_nb_with_frontend_and_backend_in_different_vpcs(test_linode_client, create_vpc_with_subnet):
    client = test_linode_client
    region = create_vpc_with_subnet[0].region
    vpc_backend = create_vpc_with_subnet[0].id
    subnet_backend = create_vpc_with_subnet[1].id
    label = get_test_label(8)
    ipv4_range = "10.0.0.0/24"
    ipv4_address = "10.0.0.2" # first available address

    vpc_frontend = client.vpcs.create(
        label=get_test_label(length=10),
        region=region,
        description="test description",
        ipv6=[{"range": "auto"}],
    )

    subnet_frontend = vpc_frontend.subnet_create(
        label="test-subnet",
        ipv4=ipv4_range,
        ipv6=[{"range": "auto"}],
    )
    ipv6_range = subnet_frontend.ipv6[0].range
    ipv6_address = ipv6_range.split("::")[0] + ":1::1"

    nb = client.nodebalancer_create(
        region=region,
        label=label,
        vpcs=[{"vpc_id": vpc_backend,"subnet_id": subnet_backend}],
        frontend_vpcs=[{"subnet_id": subnet_frontend.id, "ipv4_range": ipv4_range, "ipv6_range": ipv6_range}],
        type="premium"
    )

    assert nb.ipv4.address == ipv4_address
    assert nb.ipv6 == ipv6_address
    assert nb.frontend_address_type == 'vpc'
    assert nb.frontend_vpc_subnet_id == subnet_frontend.id

    nb_get = NodeBalancer(client, nb.id)
    nb_vpcs = nb_get.vpcs()

    assert len(nb_vpcs) == 2
    assert nb_vpcs[0].ipv4_range == f"{ipv4_address}/32"
    assert nb_vpcs[0].ipv6_range == f"{ipv6_address[:-1]}/64"
    assert nb_vpcs[0].purpose == 'frontend'
    assert nb_vpcs[1].purpose == 'backend'

    # TODO: There is no API implementation yet for /backend_vpcs and /frontend_vpcs
    # nb_backend_vpcs = nb_get.backend_vpcs()
    # assert len(nb_backend_vpcs) == 1
    # assert nb_backend_vpcs[0].purpose == 'backend'
    #
    # nb_frontend_vpcs = nb_get.frontend_vpcs()
    # assert len(nb_frontend_vpcs) == 1
    # assert nb_frontend_vpcs[0].purpose == 'frontend'

    nb.delete()
    vpc_frontend.delete()
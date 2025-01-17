import re
import time
from test.integration.conftest import get_region
from test.integration.helpers import get_test_label

import pytest

from linode_api4 import ApiError
from linode_api4.objects import ConfigInterface, ObjectStorageKeys, Region


@pytest.fixture(scope="session")
def setup_client_and_linode(test_linode_client, e2e_test_firewall):
    client = test_linode_client
    region = get_region(client, {"Kubernetes", "NodeBalancers"}, "core").id

    label = get_test_label()

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1",
        region,
        image="linode/debian12",
        label=label,
        firewall=e2e_test_firewall,
    )

    yield client, linode_instance

    linode_instance.delete()


def test_get_account(setup_client_and_linode):
    client = setup_client_and_linode[0]
    account = client.account()

    assert re.search("^$|[a-zA-Z]+", account.first_name)
    assert re.search("^$|[a-zA-Z]+", account.last_name)
    assert re.search(
        "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+.[a-zA-Z0-9-.]+$", account.email
    )
    assert re.search("^$|[a-zA-Z0-9]+", account.address_1)
    assert re.search("^$|[a-zA-Z0-9]+", account.address_2)
    assert re.search("^$|[a-zA-Z]+", account.city)
    assert re.search("^$|[a-zA-Z]+", account.state)
    assert re.search("^$|[a-zA-Z]+", account.country)
    assert re.search("^$|[a-zA-Z0-9]+", account.zip)
    if account.tax_id:
        assert re.search("^$|[0-9]+", account.tax_id)


@pytest.mark.smoke
def test_fails_to_create_domain_without_soa_email(setup_client_and_linode):
    client = setup_client_and_linode[0]

    timestamp = str(time.time_ns())
    domain_addr = timestamp + "example.com"
    try:
        domain = client.domain_create(domain=domain_addr)
    except ApiError as e:
        assert e.status == 400


@pytest.mark.smoke
def test_get_domains(test_linode_client, test_domain):
    client = test_linode_client
    domain = test_domain
    domain_dict = client.domains()

    dom_list = [i.domain for i in domain_dict]

    assert domain.domain in dom_list


@pytest.mark.smoke
def test_get_regions(test_linode_client):
    client = test_linode_client
    regions = client.regions()

    region_list = [r.id for r in regions]

    test_region = Region(client, "us-east")

    assert test_region.id in region_list
    assert test_region.site_type in ["core", "edge"]


@pytest.mark.smoke
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_image_create(setup_client_and_linode):
    client = setup_client_and_linode[0]
    linode = setup_client_and_linode[1]

    label = get_test_label()
    description = "Test description"
    tags = ["test"]
    usable_disk = [v for v in linode.disks if v.filesystem != "swap"]

    image = client.image_create(
        disk=usable_disk[0].id, label=label, description=description, tags=tags
    )

    assert image.label == label
    assert image.description == description
    assert image.tags == tags
    # size and total_size are the same because this image is not replicated
    assert image.size == image.total_size


def test_fails_to_create_image_with_non_existing_disk_id(
    setup_client_and_linode,
):
    client = setup_client_and_linode[0]

    label = get_test_label()
    description = "Test description"
    disk_id = 111111

    try:
        image_page = client.image_create(
            disk=disk_id, label=label, description=description
        )
    except ApiError as e:
        assert "Not found" in str(e.json)
        assert e.status == 404


def test_fails_to_delete_predefined_images(setup_client_and_linode):
    client = setup_client_and_linode[0]

    images = client.images()

    try:
        # new images go on top of the list thus choose last image
        images.last().delete()
    except ApiError as e:
        assert "Unauthorized" in str(e.json)
        assert e.status == 403


def test_get_volume(test_linode_client, test_volume):
    client = test_linode_client
    label = test_volume.label

    volume_dict = client.volumes()

    volume_label_list = [i.label for i in volume_dict]

    assert label in volume_label_list


def test_get_tag(test_linode_client, test_tag):
    client = test_linode_client
    label = test_tag.label

    tags = client.tags()

    tag_label_list = [i.label for i in tags]

    assert label in tag_label_list


def test_create_tag_with_id(
    setup_client_and_linode, test_nodebalancer, test_domain, test_volume
):
    client = setup_client_and_linode[0]
    linode = setup_client_and_linode[1]
    nodebalancer = test_nodebalancer
    domain = test_domain
    volume = test_volume

    label = get_test_label()

    tag = client.tag_create(
        label=label,
        instances=[linode.id, linode],
        nodebalancers=[nodebalancer.id, nodebalancer],
        domains=[domain.id, domain],
        volumes=[volume.id, volume],
    )

    # Get tags after creation
    tags = client.tags()

    tag_label_list = [i.label for i in tags]

    tag.delete()

    assert label in tag_label_list


@pytest.mark.smoke
def test_create_tag_with_entities(
    setup_client_and_linode, test_nodebalancer, test_domain, test_volume
):
    client = setup_client_and_linode[0]
    linode = setup_client_and_linode[1]
    nodebalancer = test_nodebalancer
    domain = test_domain
    volume = test_volume

    label = get_test_label()

    tag = client.tag_create(
        label, entities=[linode, domain, nodebalancer, volume]
    )

    # Get tags after creation
    tags = client.tags()

    tag_label_list = [i.label for i in tags]

    tag.delete()

    assert label in tag_label_list


# AccountGroupTests
def test_get_account_settings(test_linode_client):
    client = test_linode_client
    account_settings = client.account.settings()

    assert account_settings._populated == True
    assert re.search(
        r"'network_helper':\s*(True|False)", str(account_settings._raw_json)
    )


# TODO: Account invoice and payment test cases need to be added


# LinodeGroupTests
def test_create_linode_instance_without_image(test_linode_client):
    client = test_linode_client
    region = get_region(client, {"Linodes"}, "core").id
    label = get_test_label()

    linode_instance = client.linode.instance_create(
        "g6-nanode-1", region, label=label
    )

    assert linode_instance.label == label
    assert linode_instance.image is None

    res = linode_instance.delete()

    assert res


@pytest.mark.smoke
def test_create_linode_instance_with_image(setup_client_and_linode):
    linode = setup_client_and_linode[1]

    assert re.search("linode/debian12", str(linode.image))


def test_create_linode_with_interfaces(test_linode_client):
    client = test_linode_client
    region = get_region(client, {"Vlans", "Linodes"}, site_type="core").id
    label = get_test_label()

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1",
        region,
        label=label,
        image="linode/debian12",
        interfaces=[
            {"purpose": "public"},
            ConfigInterface(
                purpose="vlan", label="cool-vlan", ipam_address="10.0.0.4/32"
            ),
        ],
    )

    assert len(linode_instance.configs[0].interfaces) == 2
    assert linode_instance.configs[0].interfaces[0].purpose == "public"
    assert linode_instance.configs[0].interfaces[1].purpose == "vlan"
    assert linode_instance.configs[0].interfaces[1].label == "cool-vlan"
    assert (
        linode_instance.configs[0].interfaces[1].ipam_address == "10.0.0.4/32"
    )

    res = linode_instance.delete()

    assert res


# LongviewGroupTests
def test_get_longview_clients(test_linode_client, test_longview_client):
    client = test_linode_client

    longview_client = client.longview.clients()

    client_labels = [i.label for i in longview_client]

    assert test_longview_client.label in client_labels


def test_client_create_with_label(test_linode_client):
    client = test_linode_client
    label = get_test_label()
    longview_client = client.longview.client_create(label=label)

    assert label == longview_client.label

    time.sleep(5)

    res = longview_client.delete()

    assert res


# TODO: Subscription related test cases need to be added, currently returns a 404
# def test_get_subscriptions():


# LKEGroupTest


def test_kube_version(test_linode_client):
    client = test_linode_client
    lke_version = client.lke.versions()

    assert re.search("[0-9].[0-9]+", lke_version.first().id)


def test_cluster_create_with_api_objects(test_linode_client):
    client = test_linode_client
    node_type = client.linode.types()[1]  # g6-standard-1
    version = client.lke.versions()[0]
    region = get_region(client, {"Kubernetes"})
    node_pools = client.lke.node_pool(node_type, 3)
    label = get_test_label()

    cluster = client.lke.cluster_create(region, label, node_pools, version)

    assert cluster.region.id == region.id
    assert cluster.k8s_version.id == version.id

    res = cluster.delete()

    assert res


def test_fails_to_create_cluster_with_invalid_version(test_linode_client):
    invalid_version = "a.12"
    client = test_linode_client
    region = get_region(client, {"Kubernetes"}).id

    try:
        cluster = client.lke.cluster_create(
            region,
            "example-cluster",
            {"type": "g6-standard-1", "count": 3},
            invalid_version,
        )
    except ApiError as e:
        assert "not valid" in str(e.json)
        assert e.status == 400


# ObjectStorageGroupTests


def test_get_object_storage_clusters(test_linode_client):
    client = test_linode_client

    clusters = client.object_storage.clusters()

    assert "us-east" in clusters[0].id
    assert "us-east" in clusters[0].region.id


def test_get_keys(test_linode_client, access_keys_object_storage):
    client = test_linode_client
    key = access_keys_object_storage

    keys = client.object_storage.keys()
    key_labels = [i.label for i in keys]

    assert key.label in key_labels


def test_keys_create(test_linode_client, access_keys_object_storage):
    key = access_keys_object_storage

    assert type(key) == type(
        ObjectStorageKeys(client=test_linode_client, id="123")
    )


# NetworkingGroupTests


@pytest.fixture
def create_firewall_with_inbound_outbound_rules(test_linode_client):
    client = test_linode_client
    label = get_test_label() + "-firewall"
    rules = {
        "outbound": [
            {
                "ports": "22",
                "protocol": "TCP",
                "addresses": {"ipv4": ["198.0.0.2/32"]},
                "action": "ACCEPT",
                "label": "accept-inbound-SSH",
            }
        ],
        "outbound_policy": "DROP",
        "inbound": [
            {
                "ports": "22",
                "protocol": "TCP",
                "addresses": {"ipv4": ["198.0.0.2/32"]},
                "action": "ACCEPT",
                "label": "accept-inbound-SSH",
            }
        ],
        "inbound_policy": "ACCEPT",
    }

    firewall = client.networking.firewall_create(
        label, rules=rules, status="enabled"
    )

    yield firewall

    firewall.delete()


def test_get_firewalls_with_inbound_outbound_rules(
    test_linode_client, create_firewall_with_inbound_outbound_rules
):
    client = test_linode_client
    firewalls = client.networking.firewalls()
    firewall = create_firewall_with_inbound_outbound_rules

    firewall_labels = [i.label for i in firewalls]

    assert firewall.label in firewall_labels
    assert firewall.rules.inbound_policy == "ACCEPT"
    assert firewall.rules.outbound_policy == "DROP"

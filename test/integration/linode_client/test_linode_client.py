import re
import time
from test.integration.helpers import get_test_label

import pytest

from linode_api4 import ApiError, LinodeClient
from linode_api4.objects import ObjectStorageKeys


@pytest.fixture(scope="session", autouse=True)
def setup_client_and_linode(test_linode_client):
    client = test_linode_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    label = get_test_label()

    linode_instance, password = client.linode.instance_create(
        "g6-nanode-1", chosen_region, image="linode/debian10", label=label
    )

    yield client, linode_instance

    linode_instance.delete()


def test_get_account(setup_client_and_linode):
    client = setup_client_and_linode[0]
    account = client.account()

    assert re.search("^$|[a-zA-Z]+", account.first_name)
    assert re.search("^$|[a-zA-Z]+", account.last_name)
    assert re.search(
        "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", account.email
    )
    assert re.search(
        "^(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$", account.phone
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
def test_image_create(setup_client_and_linode):
    client = setup_client_and_linode[0]
    linode = setup_client_and_linode[1]

    label = get_test_label()
    description = "Test description"
    disk_id = linode.disks.first().id

    image = client.image_create(
        disk=disk_id, label=label, description=description
    )

    assert image.label == label
    assert image.description == description


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
        "'network_helper':True|False", str(account_settings._raw_json)
    )


# TODO: Account invoice and payment test cases need to be added


# LinodeGroupTests
def test_create_linode_instance_without_image(test_linode_client):
    client = test_linode_client
    available_regions = client.regions()
    chosen_region = available_regions[0]
    label = get_test_label()

    linode_instance = client.linode.instance_create(
        "g6-nanode-1", chosen_region, label=label
    )

    assert linode_instance.label == label
    assert linode_instance.image is None

    res = linode_instance.delete()

    assert res


@pytest.mark.smoke
def test_create_linode_instance_with_image(setup_client_and_linode):
    linode = setup_client_and_linode[1]

    assert re.search("linode/debian10", str(linode.image))


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
    region = client.regions().first()
    node_pools = client.lke.node_pool(node_type, 3)
    label = get_test_label() + "-cluster"

    cluster = client.lke.cluster_create(region, label, node_pools, version)

    assert cluster.region.id == region.id
    assert cluster.k8s_version.id == version.id

    res = cluster.delete()

    assert res


def test_fails_to_create_cluster_with_invalid_version(test_linode_client):
    invalid_version = "a.12"
    client = test_linode_client

    try:
        cluster = client.lke.cluster_create(
            "ap-west",
            "example-cluster",
            {"type": "g6-standard-1", "count": 3},
            invalid_version,
        )
    except ApiError as e:
        assert "not valid" in str(e.json)
        assert e.status == 400


# ProfileGroupTest


def test_get_sshkeys(test_linode_client, test_sshkey):
    client = test_linode_client

    ssh_keys = client.profile.ssh_keys()

    ssh_labels = [i.label for i in ssh_keys]

    assert test_sshkey.label in ssh_labels


def test_ssh_key_create(test_sshkey, ssh_key_gen):
    pub_key = ssh_key_gen[0]
    key = test_sshkey

    assert pub_key == key._raw_json["ssh_key"]


# ObjectStorageGroupTests


def test_get_object_storage_clusters(test_linode_client):
    client = test_linode_client

    clusters = client.object_storage.clusters()

    assert "us-east" in clusters[0].id
    assert "us-east" in clusters[0].region.id


def test_get_keys(test_linode_client, ssh_keys_object_storage):
    client = test_linode_client
    key = ssh_keys_object_storage

    keys = client.object_storage.keys()
    key_labels = [i.label for i in keys]

    assert key.label in key_labels


def test_keys_create(test_linode_client, ssh_keys_object_storage):
    key = ssh_keys_object_storage

    assert type(key) == type(
        ObjectStorageKeys(client=test_linode_client, id="123")
    )


# NetworkingGroupTests

# TODO:: creating vlans
# def test_get_vlans():


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

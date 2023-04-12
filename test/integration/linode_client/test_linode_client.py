from linode_api4 import LinodeClient
from linode_api4.objects import Instance, Disk, Domain
import pytest
from unittest import TestCase

from linode_api4 import ApiError
from helpers import create_domain, create_volume, create_tag, create_nodebalancer

import re
import time


@pytest.fixture(scope="session", autouse=True)
def setup_client_and_linode(get_client):
    client = get_client
    available_regions = client.regions()
    chosen_region = available_regions[0]

    linode_instance, password = client.linode.instance_create('g5-standard-4',
                                                     chosen_region,
                                                     image='linode/debian9')
    
    yield client, linode_instance

    linode_instance.delete()


def test_get_account(setup_client_and_linode):
    client = setup_client_and_linode[0]
    account = client.account()

    assert(re.search("[a-zA-Z]+", account.first_name))
    assert(re.search("[a-zA-Z]+", account.last_name))
    assert(re.search("^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", account.email))
    assert(re.search("^(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}$", account.phone))
    assert(re.search("[a-zA-Z0-9]+", account.address_1))
    assert(re.search("[a-zA-Z0-9]+", account.address_2))
    assert(re.search("[a-zA-Z]+", account.city))
    assert(re.search("[a-zA-Z]+",account.state))
    assert(re.search("[a-zA-Z]+",account.country))
    assert(re.search("[a-zA-Z0-9]+",account.zip))
    assert(re.search("[0-9]+",account.tax_id))


def test_fails_to_create_domain_without_soa_email(setup_client_and_linode):
    client = setup_client_and_linode[0]

    timestamp = str(int(time.time()))
    domain_addr = timestamp + "example.com"
    try:
        domain = client.domain_create(domain=domain_addr)
    except ApiError as e:
        assert e.status == 400


def test_get_domains(get_client, create_domain):
    client = get_client
    domain = create_domain
    domain_dict = client.domains()

    dom_list = [i.domain for i in domain_dict]

    assert(domain.domain in dom_list)


def test_image_create(setup_client_and_linode):
    client = setup_client_and_linode[0]
    linode = setup_client_and_linode[1]
    
    label = "Test-image"
    description = "Test description"
    disk_id = linode.disks.first().id

    image = client.image_create(disk=disk_id, label=label, description=description)

    assert image.label == label
    assert image.description == description

    image.delete()


def test_fails_to_create_image_with_non_existing_disk_id(setup_client_and_linode):
    client = setup_client_and_linode[0]
    
    label = "Test-image"
    description = "Test description"
    disk_id = 111111

    try:
        image_page = client.image_create(disk=disk_id, label=label, description=description)
    except ApiError as e:
        assert "Not found" in str(e.json)
        assert e.status == 404


def test_fails_to_delete_predefined_images(setup_client_and_linode):
    client = setup_client_and_linode[0]
    
    images = client.images() 

    try:
        # new images go on top of the list 
        images.last().delete()
    except ApiError as e:
        assert "Unauthorized" in str(e.json)
        assert e.status == 403


def test_get_volume(get_client, create_volume):
    client = get_client
    label = create_volume.label

    volume_dict = client.volumes()

    volume_label_list = [i.label for i in volume_dict]

    assert label in volume_label_list


def test_get_tag(get_client, create_tag):
    client = get_client
    label = create_tag.label

    tags = client.tags()
    
    tag_label_list = [i.label for i in tags]

    assert label in tag_label_list



def test_create_tag_with_id(setup_client_and_linode, create_nodebalancer, create_domain, create_volume):
    client = setup_client_and_linode[0]
    linode = setup_client_and_linode[1]
    nodebalancer = create_nodebalancer
    domain = create_domain
    volume = create_volume

    label= "test-tag-create-with-id"

    tag = client.tag_create(label=label, instances=[linode.id, linode], nodebalancers=[nodebalancer.id, nodebalancer], domains=[domain.id, domain], volumes=[volume.id, volume])

    # Get tags after creation
    tags = client.tags()

    tag_label_list = [i.label for i in tags]

    assert label in tag_label_list

    tag.delete()


def test_create_tag_with_entities(setup_client_and_linode, create_nodebalancer, create_domain, create_volume):
    client = setup_client_and_linode[0]
    linode = setup_client_and_linode[1]
    nodebalancer = create_nodebalancer
    domain = create_domain
    volume = create_volume

    label= "test-tag-create-with-entities"

    tag = client.tag_create(label, entities=[linode, domain, nodebalancer, volume])

    # Get tags after creation
    tags = client.tags()

    tag_label_list = [i.label for i in tags]

    assert label in tag_label_list

    tag.delete()


import pytest

from linode_api4 import VPC, LinodeClient, VPCSubnet
from linode_api4.objects import Volume


def test_get_vpc(get_client, create_vpc):
    vpc = get_client.load(VPC, create_vpc.id)

    assert vpc.id == create_vpc.id


def test_update_vpc(get_client, create_vpc):
    vpc = create_vpc
    new_label = create_vpc.label + "-updated"
    new_desc = "updated description"

    vpc.label = new_label
    vpc.description = new_desc
    vpc.save()

    vpc = get_client.load(VPC, create_vpc.id)

    assert vpc.label == new_label
    assert vpc.description == new_desc


def test_get_subnet(get_client, create_vpc_with_subnet):
    vpc, subnet = create_vpc_with_subnet
    loaded_subnet = get_client.load(VPCSubnet, subnet.id, vpc.id)

    assert loaded_subnet.id == subnet.id


def test_update_subnet(get_client, create_vpc_with_subnet):
    vpc, subnet = create_vpc_with_subnet
    new_label = subnet.label + "-updated"

    subnet.label = new_label
    subnet.save()

    subnet = get_client.load(VPCSubnet, subnet.id, vpc.id)

    assert subnet.label == new_label

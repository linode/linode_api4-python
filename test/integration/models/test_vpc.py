from test.integration.conftest import get_region

import pytest

from linode_api4 import VPC, ApiError, VPCSubnet


def test_get_vpc(test_linode_client, create_vpc):
    vpc = test_linode_client.load(VPC, create_vpc.id)
    test_linode_client.vpcs()
    assert vpc.id == create_vpc.id


def test_update_vpc(test_linode_client, create_vpc):
    vpc = create_vpc
    new_label = create_vpc.label + "-updated"
    new_desc = "updated description"

    vpc.label = new_label
    vpc.description = new_desc
    vpc.save()

    vpc = test_linode_client.load(VPC, create_vpc.id)

    assert vpc.label == new_label
    assert vpc.description == new_desc


def test_get_subnet(test_linode_client, create_vpc_with_subnet):
    vpc, subnet = create_vpc_with_subnet
    loaded_subnet = test_linode_client.load(VPCSubnet, subnet.id, vpc.id)

    assert loaded_subnet.id == subnet.id


def test_update_subnet(test_linode_client, create_vpc_with_subnet):
    vpc, subnet = create_vpc_with_subnet
    new_label = subnet.label + "-updated"

    subnet.label = new_label
    subnet.save()

    subnet = test_linode_client.load(VPCSubnet, subnet.id, vpc.id)

    assert subnet.label == new_label


def test_fails_create_vpc_invalid_data(test_linode_client):
    with pytest.raises(ApiError) as excinfo:
        test_linode_client.vpcs.create(
            label="invalid_label!!",
            region=get_region(test_linode_client, {"VPCs"}),
            description="test description",
        )
    assert excinfo.value.status == 400
    assert "Label must include only ASCII" in str(excinfo.value.json)


def test_get_all_vpcs(test_linode_client, create_multiple_vpcs):
    vpc_1, vpc_2 = create_multiple_vpcs

    all_vpcs = test_linode_client.vpcs()

    assert str(vpc_1) in str(all_vpcs.lists)
    assert str(vpc_2) in str(all_vpcs.lists)


def test_fails_update_vpc_invalid_data(create_vpc):
    vpc = create_vpc

    invalid_label = "invalid!!"
    vpc.label = invalid_label

    with pytest.raises(ApiError) as excinfo:
        vpc.save()

    assert excinfo.value.status == 400
    assert "Label must include only ASCII" in str(excinfo.value.json)


def test_fails_create_subnet_invalid_data(create_vpc):
    invalid_ipv4 = "10.0.0.0"

    with pytest.raises(ApiError) as excinfo:
        create_vpc.subnet_create("test-subnet", ipv4=invalid_ipv4)

    assert excinfo.value.status == 400
    assert "ipv4 must be an IPv4 network" in str(excinfo.value.json)


def test_fails_update_subnet_invalid_data(create_vpc_with_subnet):
    invalid_label = "invalid_subnet_label!!"
    vpc, subnet = create_vpc_with_subnet
    subnet.label = invalid_label

    with pytest.raises(ApiError) as excinfo:
        subnet.save()

    assert excinfo.value.status == 400
    assert "Label must include only ASCII" in str(excinfo.value.json)

from linode_api4 import VPC, VPCSubnet, ApiError
from test.integration.conftest import get_region


def test_get_vpc(get_client, create_vpc):
    vpc = get_client.load(VPC, create_vpc.id)
    get_client.vpc()
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


def test_fails_create_vpc_invalid_data(get_client):
    try:
       get_client.vpcs.create(label="invalid_label!!", region=get_region(get_client, {"VPCs"}), description="test description")
    except ApiError as e:
        assert e.status == 400
        assert 'Label must include only ASCII letters, numbers, and dashes' in str(e.json)


def test_get_all_vpcs(get_client, create_multiple_vpcs):
    vpc_1, vpc_2 = create_multiple_vpcs

    all_vpcs = get_client.vpcs()

    assert str(vpc_1) in str(all_vpcs.lists)
    assert str(vpc_2) in str(all_vpcs.lists)


def test_fails_update_vpc_invalid_data(create_vpc):
    vpc = create_vpc

    invalid_label = "invalid!!"

    try:
        vpc.label = invalid_label
        vpc.save()
    except ApiError as e:
        assert e.status == 400
        assert 'Label must include only ASCII letters, numbers, and dashes' in str(e.json)


def test_fails_create_subnet_invalid_data(create_vpc):
    invalid_ipv4 = "10.0.0.0"
    try:
        create_vpc.subnet_create("test-subnet", ipv4=invalid_ipv4)
    except ApiError as e:
        assert e.status == 400
        assert 'ipv4 must be an IPv4 network with at least 8 addresses, but it had only 1' in str(e.json)


def test_fails_update_subnet_invalid_data(create_vpc_with_subnet):
    invalid_label = "invalid_subnet_label!!"
    vpc, subnet = create_vpc_with_subnet
    try:
        subnet.label = invalid_label
        subnet.save()
    except ApiError as e:
        assert e.status == 400
        assert 'Label must include only ASCII letters, numbers, and dashes' in str(e.json)



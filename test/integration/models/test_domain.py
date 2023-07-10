import re
import time
from test.integration.helpers import wait_for_condition

import pytest

from linode_api4.objects import Domain, DomainRecord


@pytest.mark.smoke
def test_get_domain_record(get_client, create_domain):
    dr = DomainRecord(
        get_client, create_domain.records.first().id, create_domain.id
    )

    assert dr.id == create_domain.records.first().id


def test_save_null_values_excluded(get_client, create_domain):
    domain = get_client.load(Domain, create_domain.id)

    domain.type = "master"
    domain.master_ips = ["127.0.0.1"]
    res = domain.save()

    assert res


def test_zone_file_view(get_client, create_domain):
    domain = get_client.load(Domain, create_domain.id)

    def get_zone_file_view():
        res = domain.zone_file_view()
        return res != []

    wait_for_condition(10, 100, get_zone_file_view)

    assert domain.domain in str(domain.zone_file_view())
    assert re.search("ns[0-9].linode.com", str(domain.zone_file_view()))


def test_clone(get_client, create_domain):
    domain = get_client.load(Domain, create_domain.id)
    timestamp = str(int(time.time()))
    dom = "example.clone-" + timestamp + "-IntTestSDK.org"
    domain.clone(dom)

    ds = get_client.domains()

    time.sleep(1)

    domains = [i.domain for i in ds]

    assert dom in domains


def test_import(get_client, create_domain):
    pytest.skip(
        'Currently failing with message: linode_api4.errors.ApiError: 400: An unknown error occured. Please open a ticket for further assistance. Command: domain_import(domain, "google.ca")'
    )
    domain = get_client.load(Domain, create_domain.id)

import os
import pytest
from linode_api4.linode_client import LinodeClient


ENV_TOKEN_NAME = "LINODE_CLI_TOKEN"

def get_token():
    return os.environ.get(ENV_TOKEN_NAME, None)


@pytest.fixture(scope="session", autouse=True)
def get_client():
    token = get_token()
    client = LinodeClient(token)
    return client


@pytest.fixture(scope="session", autouse=True)
def set_up_account(get_client):
    client = get_client
    account = client.account()

    account.first_name = "Test"
    account.last_name = "User"
    account.email = "test-123@linode.com"
    account.phone = "111-111-1111"
    account.address_1 = "3rd & Arch St"
    account.address_2 = "Unit 999"
    account.city = "Philadelphia"
    account.state = "PA"
    account.country = "US"
    account.zip = "19106"
    account.tax_id = "999-99-9999"

    account.save()



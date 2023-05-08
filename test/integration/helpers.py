import random
import time
from typing import Callable

from linode_api4 import PaginatedList
from linode_api4.linode_client import LinodeClient
from linode_api4.errors import ApiError


def get_test_label():
    unique_timestamp = str(int(time.time()) + random.randint(0, 1000))
    label = "IntTestSDK_" + unique_timestamp
    return label


def delete_instance_with_test_kw(paginated_list: PaginatedList):
    for i in paginated_list:
        try:
            if hasattr(i, "label"):
                label = getattr(i, "label")
                if "IntTestSDK" in str(label):
                    i.delete()
                elif "lke" in str(label):
                    iso_created_date = getattr(i, "created")
                    created_time = int(
                        time.mktime(iso_created_date.timetuple())
                    )
                    timestamp = int(time.time())
                    if (timestamp - created_time) < 86400:
                        i.delete()
            elif hasattr(i, "domain"):
                domain = getattr(i, "domain")
                if "IntTestSDK" in domain:
                    i.delete()
        except AttributeError as e:
            if "IntTestSDK" in str(i.__dict__):
                i.delete()


def delete_all_test_instances(client: LinodeClient):
    tags = client.tags()
    linodes = client.linode.instances()
    images = client.images()
    volumes = client.volumes()
    nodebalancers = client.nodebalancers()
    domains = client.domains()
    longview_clients = client.longview.clients()
    clusters = client.lke.clusters()
    firewalls = client.networking.firewalls()

    delete_instance_with_test_kw(tags)
    delete_instance_with_test_kw(linodes)
    delete_instance_with_test_kw(images)
    delete_instance_with_test_kw(volumes)
    delete_instance_with_test_kw(nodebalancers)
    delete_instance_with_test_kw(domains)
    delete_instance_with_test_kw(longview_clients)
    delete_instance_with_test_kw(clusters)
    delete_instance_with_test_kw(firewalls)


def wait_for_condition(
    interval: int, timeout: int, condition: Callable, *args
) -> object:
    start_time = time.time()
    while True:
        if condition(*args):
            break

        if time.time() - start_time > timeout:
            raise TimeoutError("Wait for condition timeout error")

        time.sleep(interval)


# Retry function to help in case of requests sending too quickly before instance is ready
def retry_sending_request(
    retries: int, condition: Callable, *args
) -> object:
    curr_t = 0
    while curr_t < retries:
        try:
            if condition(*args):
                break
        except ApiError:
            if curr_t >= retries:
                raise ApiError
        curr_t += 1


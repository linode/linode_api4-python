import pytest
import time
import random
from linode_api4.linode_client import LinodeClient 
from linode_api4 import Instance
from linode_api4 import PaginatedList


def get_test_label():
    unique_timestamp = str(int(time.time()) + random.randint(0, 1000))
    label = "IntTestSDK-"+ unique_timestamp
    return label

def delete_instance_with_test_label(paginated_list: PaginatedList):
    print("deleting instace: ", paginated_list )
    for i in paginated_list:
        if "IntTestSDK" in str(i.__dict__):
            try:
                i.delete()
            except e:
                print("failed deleting", i)

def delete_all_test_instances(client: LinodeClient):
    tags = client.tags()
    linodes = client.linode.instances()
    images = client.images()
    volumes = client.volumes()
    nodebalancers = client.nodebalancers()
    domains = client.domains()
    longview_clients = client.longview.clients()
    clusters = client.lke.clusters()

    delete_instance_with_test_label(tags)
    delete_instance_with_test_label(linodes)
    delete_instance_with_test_label(images)
    delete_instance_with_test_label(volumes)
    delete_instance_with_test_label(nodebalancers)
    delete_instance_with_test_label(domains)
    delete_instance_with_test_label(longview_clients)
    delete_instance_with_test_label(clusters)
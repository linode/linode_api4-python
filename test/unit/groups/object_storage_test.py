import pytest

from linode_api4.groups.object_storage import ObjectStorageGroup


@pytest.mark.parametrize(
    "cluster_or_region,is_cluster",
    [
        ("us-east-1", True),
        ("us-central-1", True),
        ("us-mia-1", True),
        ("us-iad-123", True),
        ("us-east", False),
        ("us-central", False),
        ("us-mia", False),
        ("us-iad", False),
    ],
)
def test_is_cluster(cluster_or_region: str, is_cluster: bool):
    assert ObjectStorageGroup.is_cluster(cluster_or_region) == is_cluster

from io import BytesIO
from test.integration.conftest import get_region, get_regions
from test.integration.helpers import get_test_label

import polling
import pytest

from linode_api4.objects import Image


@pytest.fixture(scope="session")
def image_upload_url(test_linode_client):
    label = get_test_label() + "_image"

    region = get_region(
        test_linode_client,
        capabilities={"Linodes", "Object Storage"},
        site_type="core",
    )

    test_linode_client.image_create_upload(
        label, region.id, "integration test image upload"
    )

    image = test_linode_client.images()[0]

    yield image

    image.delete()


@pytest.fixture(scope="session")
def test_uploaded_image(test_linode_client):
    test_image_content = (
        b"\x1f\x8b\x08\x08\xbd\x5c\x91\x60\x00\x03\x74\x65\x73\x74\x2e\x69"
        b"\x6d\x67\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    )

    label = get_test_label() + "_image"

    regions = get_regions(
        test_linode_client, capabilities={"Object Storage"}, site_type="core"
    )

    image = test_linode_client.image_upload(
        label,
        regions[1].id,
        BytesIO(test_image_content),
        description="integration test image upload",
        tags=["tests"],
    )

    yield image, regions

    image.delete()


@pytest.mark.smoke
def test_get_image(test_linode_client, image_upload_url):
    image = test_linode_client.load(Image, image_upload_url.id)

    assert image.label == image_upload_url.label


def test_image_create_upload(test_linode_client, test_uploaded_image):
    uploaded_image, _ = test_uploaded_image

    image = test_linode_client.load(Image, uploaded_image.id)

    assert image.label == uploaded_image.label
    assert image.description == "integration test image upload"
    assert image.tags[0] == "tests"


@pytest.mark.smoke
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_image_replication(test_linode_client, test_uploaded_image):
    uploaded_image, regions = test_uploaded_image

    image = test_linode_client.load(Image, uploaded_image.id)

    # wait for image to be available for replication
    def poll_func() -> bool:
        image._api_get()
        return image.status in {"available"}

    try:
        polling.poll(
            poll_func,
            step=10,
            timeout=250,
        )
    except polling.TimeoutException:
        print("failed to wait for image status: timeout period expired.")

    replicate_regions = [r.id for r in regions[:2]]
    image.replicate(replicate_regions)

    assert image.label == uploaded_image.label
    assert len(image.regions) == 2
    assert image.regions[0].region in replicate_regions
    assert image.regions[1].region in replicate_regions

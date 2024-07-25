from io import BytesIO
from test.integration.helpers import (
    delete_instance_with_test_kw,
    get_test_label,
)

import polling
import pytest

from linode_api4.objects import Image


@pytest.fixture(scope="session")
def image_upload_url(test_linode_client):
    label = get_test_label() + "_image"

    # TODO: use get_region to get regions randomly with specific functionality
    # region = get_region(test_linode_client, {"Functionality"})

    test_linode_client.image_create_upload(
        label, "us-east", "integration test image upload"
    )

    image = test_linode_client.images()[0]

    yield image

    image.delete()
    images = test_linode_client.images()
    delete_instance_with_test_kw(images)


@pytest.fixture(scope="session")
def test_uploaded_image(test_linode_client):
    test_image_content = (
        b"\x1F\x8B\x08\x08\xBD\x5C\x91\x60\x00\x03\x74\x65\x73\x74\x2E\x69"
        b"\x6D\x67\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    )

    label = get_test_label() + "_image"
    image = test_linode_client.image_upload(
        label,
        "us-east",
        BytesIO(test_image_content),
        description="integration test image upload",
        tags=["tests"],
    )

    yield image

    image.delete()


@pytest.mark.smoke
def test_get_image(test_linode_client, image_upload_url):
    image = test_linode_client.load(Image, image_upload_url.id)

    assert image.label == image_upload_url.label


def test_image_create_upload(test_linode_client, test_uploaded_image):
    image = test_linode_client.load(Image, test_uploaded_image.id)

    assert image.label == test_uploaded_image.label
    assert image.description == "integration test image upload"
    assert image.tags[0] == "tests"


# TODO: Image is not ready for replication yet. We'll verify this test when the API is ready.
@pytest.mark.smoke
def test_image_replication(test_linode_client, test_uploaded_image):
    image = test_linode_client.load(Image, test_uploaded_image.id)

    # wait for image to be available for replication
    def poll_func() -> bool:
        image._api_get()
        return image.status in {"available"}

    try:
        polling.poll(
            poll_func,
            step=10,
            timeout=100,
        )
    except polling.TimeoutException:
        print("failed to wait for image status: timeout period expired.")

    image.replicate(["us-east", "eu-west"])

    assert image.label == test_uploaded_image.label
    assert len(image.regions) == 2

from io import BytesIO
from test.integration.helpers import (
    delete_instance_with_test_kw,
    get_test_label,
)

import pytest

from linode_api4.objects import Image


@pytest.fixture(scope="session")
def image_upload(test_linode_client):
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


@pytest.mark.smoke
def test_get_image(test_linode_client, image_upload):
    image = test_linode_client.load(Image, image_upload.id)

    assert image.label == image_upload.label


def test_image_create_upload(test_linode_client):
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

    assert image.label == label
    assert image.description == "integration test image upload"
    assert image.tags[0] == "tests"


# TODO: Image is not ready for replication yet. We'll verify this test when the API is ready.
@pytest.mark.smoke
def test_image_replication(test_linode_client, image_upload):
    image = test_linode_client.load(Image, image_upload.id)

    image.replicate("us-central")

    assert image.label == image_upload.label
    assert image.total_size == image_upload.size * 2
    assert len(image.regions) == 2

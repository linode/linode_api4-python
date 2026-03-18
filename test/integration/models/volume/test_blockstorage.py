from test.integration.conftest import get_region
from test.integration.helpers import get_test_label, retry_sending_request


def test_config_create_with_extended_volume_limit(test_linode_client):
    client = test_linode_client

    region = get_region(client, {"Linodes", "Block Storage"}, site_type="core")
    label = get_test_label()

    linode, _ = client.linode.instance_create(
        "g6-standard-6",
        region,
        image="linode/debian12",
        label=label,
    )

    volumes = [
        client.volume_create(
            f"{label}-vol-{i}",
            region=region,
            size=10,
        )
        for i in range(12)
    ]

    config = linode.config_create(volumes=volumes)

    devices = config._raw_json["devices"]

    assert len([d for d in devices.values() if d is not None]) == 12

    assert "sdi" in devices
    assert "sdj" in devices
    assert "sdk" in devices
    assert "sdl" in devices

    linode.delete()
    for v in volumes:
        retry_sending_request(3, v.delete)

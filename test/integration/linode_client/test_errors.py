from linode_api4.errors import ApiError


def test_error_404(test_linode_client):
    api_exc = None

    try:
        test_linode_client.get("/invalid/endpoint")
    except ApiError as exc:
        api_exc = exc

    assert str(api_exc) == "GET /v4beta/invalid/endpoint: [404] Not found"


def test_error_400(test_linode_client):
    api_exc = None

    try:
        test_linode_client.linode.instance_create(
            "g6-fake-plan", "us-fakeregion"
        )
    except ApiError as exc:
        api_exc = exc

    assert str(api_exc) == (
        "POST /v4beta/linode/instances: [400] type: A valid plan type by that ID was not found; "
        "region: region is not valid"
    )

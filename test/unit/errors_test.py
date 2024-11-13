from types import SimpleNamespace
from unittest import TestCase

from linode_api4.errors import ApiError, UnexpectedResponseError


class ApiErrorTest(TestCase):
    def test_from_response(self):
        mock_response = SimpleNamespace(
            status_code=400,
            json=lambda: {
                "errors": [
                    {"reason": "foo"},
                    {"field": "bar", "reason": "oh no"},
                ]
            },
            text='{"errors": [{"reason": "foo"}, {"field": "bar", "reason": "oh no"}]}',
            request=SimpleNamespace(
                method="POST",
                path_url="foo/bar",
            ),
        )

        exc = ApiError.from_response(mock_response)

        assert str(exc) == "POST foo/bar: [400] foo; bar: oh no"
        assert exc.status == 400
        assert exc.json == {
            "errors": [{"reason": "foo"}, {"field": "bar", "reason": "oh no"}]
        }
        assert exc.response.request.method == "POST"
        assert exc.response.request.path_url == "foo/bar"

    def test_from_response_non_json_body(self):
        mock_response = SimpleNamespace(
            status_code=500,
            json=lambda: None,
            text="foobar",
            request=SimpleNamespace(
                method="POST",
                path_url="foo/bar",
            ),
        )

        exc = ApiError.from_response(mock_response)

        assert str(exc) == "POST foo/bar: [500] foobar"
        assert exc.status == 500
        assert exc.json is None
        assert exc.response.request.method == "POST"
        assert exc.response.request.path_url == "foo/bar"

    def test_from_response_empty_body(self):
        mock_response = SimpleNamespace(
            status_code=500,
            json=lambda: None,
            text=None,
            request=SimpleNamespace(
                method="POST",
                path_url="foo/bar",
            ),
        )

        exc = ApiError.from_response(mock_response)

        assert str(exc) == "POST foo/bar: [500] N/A"
        assert exc.status == 500
        assert exc.json is None
        assert exc.response.request.method == "POST"
        assert exc.response.request.path_url == "foo/bar"

    def test_from_response_no_request(self):
        mock_response = SimpleNamespace(
            status_code=500, json=lambda: None, text="foobar", request=None
        )

        exc = ApiError.from_response(mock_response)

        assert str(exc) == "[500] foobar"
        assert exc.status == 500
        assert exc.json is None
        assert exc.response.request is None


class UnexpectedResponseErrorTest(TestCase):
    def test_from_response(self):
        mock_response = SimpleNamespace(
            status_code=400,
            json=lambda: {
                "foo": "bar",
            },
            request=SimpleNamespace(
                method="POST",
                path_url="foo/bar",
            ),
        )

        exc = UnexpectedResponseError.from_response("foobar", mock_response)

        assert str(exc) == "foobar"
        assert exc.status == 400
        assert exc.json == {"foo": "bar"}
        assert exc.response.request.method == "POST"
        assert exc.response.request.path_url == "foo/bar"

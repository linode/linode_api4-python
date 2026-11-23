import json
from test.unit.base import ClientBaseCase

from linode_api4 import Instance, and_, or_


class FilteringTest(ClientBaseCase):
    """
    Tests combining filters and passing them to collection methods
    """

    def test_and_two_filters(self):
        """
        Tests that and_ combines two filters
        """
        f = and_(Instance.label == "web", Instance.region == "us-east")

        self.assertEqual(
            f.dct, {"+and": [{"label": "web"}, {"region": "us-east"}]}
        )

    def test_and_many_filters(self):
        """
        Tests that and_ accepts more than two filters
        """
        f = and_(
            Instance.label == "web",
            Instance.region == "us-east",
            Instance.tags.contains("prod"),
            or_(Instance.group == "a", Instance.group == "b"),
        )

        self.assertEqual(
            f.dct,
            {
                "+and": [
                    {"label": "web"},
                    {"region": "us-east"},
                    {"tags": {"+contains": "prod"}},
                    {"+or": [{"group": "a"}, {"group": "b"}]},
                ]
            },
        )

    def test_and_requires_two_filters(self):
        """
        Tests that and_ still requires at least two filters
        """
        with self.assertRaises(TypeError):
            and_(
                Instance.label == "web"
            )  # pylint: disable=no-value-for-parameter

    def test_collection_with_many_filters(self):
        """
        Tests that a collection method accepts more than two filters and
        sends all of them in the X-Filter header
        """
        cases = (
            (
                (Instance.label == "web",),
                {"label": "web"},
            ),
            (
                (Instance.label == "web", Instance.region == "us-east"),
                {"+and": [{"label": "web"}, {"region": "us-east"}]},
            ),
            (
                (
                    Instance.label == "web",
                    Instance.region == "us-east",
                    Instance.tags.contains("prod"),
                ),
                {
                    "+and": [
                        {"label": "web"},
                        {"region": "us-east"},
                        {"tags": {"+contains": "prod"}},
                    ]
                },
            ),
        )

        for filters, expected in cases:
            with self.mock_get("linode/instances") as m:
                self.client.linode.instances(*filters)

                self.assertEqual(
                    json.loads(m.call_headers["X-Filter"]), expected
                )

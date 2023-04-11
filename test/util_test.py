import unittest

from linode_api4.util import drop_null_keys


class UtilTest(unittest.TestCase):
    """
    Tests for utility functions.
    """

    def test_drop_null_keys_nonrecursive(self):
        """
        Tests whether a non-recursive drop_null_keys call works as expected.
        """
        value = {
            "foo": "bar",
            "test": None,
            "cool": {
                "test": "bar",
                "cool": None,
            },
        }

        expected_output = {"foo": "bar", "cool": {"test": "bar", "cool": None}}

        assert drop_null_keys(value, recursive=False) == expected_output

    def test_drop_null_keys_recursive(self):
        """
        Tests whether a recursive drop_null_keys call works as expected.
        """

        value = {
            "foo": "bar",
            "test": None,
            "cool": {
                "test": "bar",
                "cool": None,
                "list": [{"foo": "bar", "test": None}],
            },
        }

        expected_output = {
            "foo": "bar",
            "cool": {
                "test": "bar",
                "list": [
                    {
                        "foo": "bar",
                    }
                ],
            },
        }

        assert drop_null_keys(value) == expected_output

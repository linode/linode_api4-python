import unittest

from linode_api4.util import drop_null_keys, generate_device_suffixes


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

    def test_generate_device_suffixes(self):
        """
        Tests whether generate_device_suffixes works as expected.
        """

        expected_output_12 = [
            "a",
            "b",
            "c",
            "d",
            "e",
            "f",
            "g",
            "h",
            "i",
            "j",
            "k",
            "l",
        ]
        assert generate_device_suffixes(12) == expected_output_12

        expected_output_30 = [
            "a",
            "b",
            "c",
            "d",
            "e",
            "f",
            "g",
            "h",
            "i",
            "j",
            "k",
            "l",
            "m",
            "n",
            "o",
            "p",
            "q",
            "r",
            "s",
            "t",
            "u",
            "v",
            "w",
            "x",
            "y",
            "z",
            "aa",
            "ab",
            "ac",
            "ad",
        ]
        assert generate_device_suffixes(30) == expected_output_30

        expected_output_60 = [
            "a",
            "b",
            "c",
            "d",
            "e",
            "f",
            "g",
            "h",
            "i",
            "j",
            "k",
            "l",
            "m",
            "n",
            "o",
            "p",
            "q",
            "r",
            "s",
            "t",
            "u",
            "v",
            "w",
            "x",
            "y",
            "z",
            "aa",
            "ab",
            "ac",
            "ad",
            "ae",
            "af",
            "ag",
            "ah",
            "ai",
            "aj",
            "ak",
            "al",
            "am",
            "an",
            "ao",
            "ap",
            "aq",
            "ar",
            "as",
            "at",
            "au",
            "av",
            "aw",
            "ax",
            "ay",
            "az",
            "ba",
            "bb",
            "bc",
            "bd",
            "be",
            "bf",
            "bg",
            "bh",
        ]
        assert generate_device_suffixes(60) == expected_output_60

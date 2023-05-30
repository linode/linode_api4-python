from unittest import TestCase

from linode_api4 import MappedObject


class MappedObjectCase(TestCase):
    def test_mapped_object_dict(self):
        test_dict = {
            "key1": 1,
            "key2": "2",
            "key3": 3.3,
            "key4": [41, "42", {"key4-3": "43"}],
            "key5": {
                "key5-1": 1,
                "key5-2": {"key5-2-1": {"key5-2-1-1": 1}},
                "key5-3": [{"key5-3-1": 531}, {"key5-3-2": 532}],
            },
        }

        mapped_obj = MappedObject(**test_dict)
        self.assertEqual(mapped_obj.dict, test_dict)

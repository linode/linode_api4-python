from dataclasses import dataclass
from test.unit.base import ClientBaseCase

from linode_api4.objects import Base, JSONObject, MappedObject, Property


class MappedObjectCase(ClientBaseCase):
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

    def test_serialize_base_objects(self):
        test_property_name = "bar"
        test_property_value = "bar"

        class Foo(Base):
            api_endpoint = "/testmappedobj1"
            id_attribute = test_property_name
            properties = {
                test_property_name: Property(mutable=True),
            }

        foo = Foo(self.client, test_property_value)
        foo._api_get()

        expected_dict = {
            "foo": {
                test_property_name: test_property_value,
            }
        }

        mapped_obj = MappedObject(foo=foo)
        self.assertEqual(mapped_obj.dict, expected_dict)

    def test_serialize_json_objects(self):
        test_property_name = "bar"
        test_property_value = "bar"

        @dataclass
        class Foo(JSONObject):
            bar: str = ""

        foo = Foo.from_json({test_property_name: test_property_value})

        expected_dict = {
            "foo": {
                test_property_name: test_property_value,
            }
        }

        mapped_obj = MappedObject(foo=foo)
        self.assertEqual(mapped_obj.dict, expected_dict)

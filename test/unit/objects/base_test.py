from dataclasses import dataclass
from test.unit.base import ClientBaseCase

from linode_api4.objects import Base, JSONObject, MappedObject, Property
from linode_api4.objects.base import (
    ExplicitNullValue,
    _flatten_request_body_recursive,
)


class FlattenRequestBodyRecursiveCase(ClientBaseCase):
    """Test cases for _flatten_request_body_recursive function"""

    def test_flatten_primitive_types(self):
        """Test that primitive types are returned as-is"""
        self.assertEqual(_flatten_request_body_recursive(123), 123)
        self.assertEqual(_flatten_request_body_recursive("test"), "test")
        self.assertEqual(_flatten_request_body_recursive(3.14), 3.14)
        self.assertEqual(_flatten_request_body_recursive(True), True)
        self.assertEqual(_flatten_request_body_recursive(False), False)
        self.assertEqual(_flatten_request_body_recursive(None), None)

    def test_flatten_dict(self):
        """Test that dicts are recursively flattened"""
        test_dict = {"key1": "value1", "key2": 123, "key3": True}
        result = _flatten_request_body_recursive(test_dict)
        self.assertEqual(result, test_dict)

    def test_flatten_nested_dict(self):
        """Test that nested dicts are recursively flattened"""
        test_dict = {
            "level1": {
                "level2": {"level3": "value", "number": 42},
                "string": "test",
            },
            "array": [1, 2, 3],
        }
        result = _flatten_request_body_recursive(test_dict)
        self.assertEqual(result, test_dict)

    def test_flatten_list(self):
        """Test that lists are recursively flattened"""
        test_list = [1, "two", 3.0, True]
        result = _flatten_request_body_recursive(test_list)
        self.assertEqual(result, test_list)

    def test_flatten_nested_list(self):
        """Test that nested lists are recursively flattened"""
        test_list = [[1, 2], [3, [4, 5]], "string"]
        result = _flatten_request_body_recursive(test_list)
        self.assertEqual(result, test_list)

    def test_flatten_base_object(self):
        """Test that Base objects are flattened to their ID"""

        class TestBase(Base):
            api_endpoint = "/test/{id}"
            properties = {
                "id": Property(identifier=True),
                "label": Property(mutable=True),
            }

        obj = TestBase(self.client, 123)
        result = _flatten_request_body_recursive(obj)
        self.assertEqual(result, 123)

    def test_flatten_base_object_in_dict(self):
        """Test that Base objects in dicts are flattened to their ID"""

        class TestBase(Base):
            api_endpoint = "/test/{id}"
            properties = {
                "id": Property(identifier=True),
                "label": Property(mutable=True),
            }

        obj = TestBase(self.client, 456)
        test_dict = {"resource": obj, "name": "test"}
        result = _flatten_request_body_recursive(test_dict)
        self.assertEqual(result, {"resource": 456, "name": "test"})

    def test_flatten_base_object_in_list(self):
        """Test that Base objects in lists are flattened to their ID"""

        class TestBase(Base):
            api_endpoint = "/test/{id}"
            properties = {
                "id": Property(identifier=True),
                "label": Property(mutable=True),
            }

        obj1 = TestBase(self.client, 111)
        obj2 = TestBase(self.client, 222)
        test_list = [obj1, "middle", obj2]
        result = _flatten_request_body_recursive(test_list)
        self.assertEqual(result, [111, "middle", 222])

    def test_flatten_explicit_null_instance(self):
        """Test that ExplicitNullValue instances are converted to None"""
        result = _flatten_request_body_recursive(ExplicitNullValue())
        self.assertIsNone(result)

    def test_flatten_explicit_null_class(self):
        """Test that ExplicitNullValue class is converted to None"""
        result = _flatten_request_body_recursive(ExplicitNullValue)
        self.assertIsNone(result)

    def test_flatten_explicit_null_in_dict(self):
        """Test that ExplicitNullValue in dicts is converted to None"""
        test_dict = {
            "field1": "value",
            "field2": ExplicitNullValue(),
            "field3": ExplicitNullValue,
        }
        result = _flatten_request_body_recursive(test_dict)
        self.assertEqual(
            result, {"field1": "value", "field2": None, "field3": None}
        )

    def test_flatten_explicit_null_in_list(self):
        """Test that ExplicitNullValue in lists is converted to None"""
        test_list = ["value", ExplicitNullValue(), ExplicitNullValue, 123]
        result = _flatten_request_body_recursive(test_list)
        self.assertEqual(result, ["value", None, None, 123])

    def test_flatten_mapped_object(self):
        """Test that MappedObject is serialized"""
        mapped_obj = MappedObject(key1="value1", key2=123)
        result = _flatten_request_body_recursive(mapped_obj)
        self.assertEqual(result, {"key1": "value1", "key2": 123})

    def test_flatten_mapped_object_nested(self):
        """Test that nested MappedObject is serialized"""
        mapped_obj = MappedObject(
            outer="value", inner={"nested_key": "nested_value"}
        )
        result = _flatten_request_body_recursive(mapped_obj)
        # The inner dict becomes a MappedObject when created
        self.assertIn("outer", result)
        self.assertEqual(result["outer"], "value")
        self.assertIn("inner", result)

    def test_flatten_mapped_object_in_dict(self):
        """Test that MappedObject in dicts is serialized"""
        mapped_obj = MappedObject(key="value")
        test_dict = {"field": mapped_obj, "other": "data"}
        result = _flatten_request_body_recursive(test_dict)
        self.assertEqual(result, {"field": {"key": "value"}, "other": "data"})

    def test_flatten_mapped_object_in_list(self):
        """Test that MappedObject in lists is serialized"""
        mapped_obj = MappedObject(key="value")
        test_list = [mapped_obj, "string", 123]
        result = _flatten_request_body_recursive(test_list)
        self.assertEqual(result, [{"key": "value"}, "string", 123])

    def test_flatten_json_object(self):
        """Test that JSONObject subclasses are serialized"""

        @dataclass
        class TestJSONObject(JSONObject):
            field1: str = ""
            field2: int = 0

        json_obj = TestJSONObject.from_json({"field1": "test", "field2": 42})
        result = _flatten_request_body_recursive(json_obj)
        self.assertEqual(result, {"field1": "test", "field2": 42})

    def test_flatten_json_object_in_dict(self):
        """Test that JSONObject in dicts is serialized"""

        @dataclass
        class TestJSONObject(JSONObject):
            name: str = ""

        json_obj = TestJSONObject.from_json({"name": "test"})
        test_dict = {"obj": json_obj, "value": 123}
        result = _flatten_request_body_recursive(test_dict)
        self.assertEqual(result, {"obj": {"name": "test"}, "value": 123})

    def test_flatten_json_object_in_list(self):
        """Test that JSONObject in lists is serialized"""

        @dataclass
        class TestJSONObject(JSONObject):
            id: int = 0

        json_obj = TestJSONObject.from_json({"id": 999})
        test_list = [json_obj, "text"]
        result = _flatten_request_body_recursive(test_list)
        self.assertEqual(result, [{"id": 999}, "text"])

    def test_flatten_complex_nested_structure(self):
        """Test a complex nested structure with multiple types"""

        class TestBase(Base):
            api_endpoint = "/test/{id}"
            properties = {
                "id": Property(identifier=True),
            }

        @dataclass
        class TestJSONObject(JSONObject):
            value: str = ""

        base_obj = TestBase(self.client, 555)
        mapped_obj = MappedObject(key="mapped")
        json_obj = TestJSONObject.from_json({"value": "json"})

        complex_structure = {
            "base": base_obj,
            "mapped": mapped_obj,
            "json": json_obj,
            "null": ExplicitNullValue(),
            "list": [base_obj, mapped_obj, json_obj, ExplicitNullValue],
            "nested": {
                "deep": {
                    "base": base_obj,
                    "primitives": [1, "two", 3.0],
                }
            },
        }

        result = _flatten_request_body_recursive(complex_structure)

        self.assertEqual(result["base"], 555)
        self.assertEqual(result["mapped"], {"key": "mapped"})
        self.assertEqual(result["json"], {"value": "json"})
        self.assertIsNone(result["null"])
        self.assertEqual(
            result["list"], [555, {"key": "mapped"}, {"value": "json"}, None]
        )
        self.assertEqual(result["nested"]["deep"]["base"], 555)
        self.assertEqual(
            result["nested"]["deep"]["primitives"], [1, "two", 3.0]
        )

    def test_flatten_with_is_put_false(self):
        """Test that is_put parameter is passed through"""

        @dataclass
        class TestJSONObject(JSONObject):
            field: str = ""

            def _serialize(self, is_put=False):
                return {"field": self.field, "is_put": is_put}

        json_obj = TestJSONObject.from_json({"field": "test"})
        result = _flatten_request_body_recursive(json_obj, is_put=False)
        self.assertEqual(result, {"field": "test", "is_put": False})

    def test_flatten_with_is_put_true(self):
        """Test that is_put=True parameter is passed through"""

        @dataclass
        class TestJSONObject(JSONObject):
            field: str = ""

            def _serialize(self, is_put=False):
                return {"field": self.field, "is_put": is_put}

        json_obj = TestJSONObject.from_json({"field": "test"})
        result = _flatten_request_body_recursive(json_obj, is_put=True)
        self.assertEqual(result, {"field": "test", "is_put": True})

    def test_flatten_empty_dict(self):
        """Test that empty dicts are handled correctly"""
        result = _flatten_request_body_recursive({})
        self.assertEqual(result, {})

    def test_flatten_empty_list(self):
        """Test that empty lists are handled correctly"""
        result = _flatten_request_body_recursive([])
        self.assertEqual(result, [])

    def test_flatten_dict_with_none_values(self):
        """Test that None values in dicts are preserved"""
        test_dict = {"key1": "value", "key2": None, "key3": 0}
        result = _flatten_request_body_recursive(test_dict)
        self.assertEqual(result, test_dict)

    def test_flatten_list_with_none_values(self):
        """Test that None values in lists are preserved"""
        test_list = ["value", None, 0, ""]
        result = _flatten_request_body_recursive(test_list)
        self.assertEqual(result, test_list)

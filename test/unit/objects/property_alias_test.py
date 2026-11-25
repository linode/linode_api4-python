"""
Tests for Property alias_of functionality
"""

from test.unit.base import ClientBaseCase

from linode_api4.objects import Base, Property


class PropertyAliasTest(ClientBaseCase):
    """Test cases for Property alias_of parameter"""

    def test_alias_populate_from_json(self):
        """Test that aliased properties are populated correctly from JSON"""

        class TestModel(Base):
            api_endpoint = "/test/{id}"
            properties = {
                "id": Property(identifier=True),
                "service_class": Property(mutable=True, alias_of="class"),
                "label": Property(mutable=True),
            }

        json_data = {
            "id": 123,
            "class": "premium",
            "label": "test-label",
        }

        obj = TestModel(self.client, 123, json_data)

        # The aliased property should be set using the Python-friendly name
        self.assertEqual(obj.service_class, "premium")
        self.assertEqual(obj.label, "test-label")

    def test_alias_serialize(self):
        """Test that aliased properties serialize back to original API names"""

        class TestModel(Base):
            api_endpoint = "/test/{id}"
            properties = {
                "id": Property(identifier=True),
                "service_class": Property(mutable=True, alias_of="class"),
                "label": Property(mutable=True),
            }

        obj = TestModel(self.client, 123)
        obj._set("service_class", "premium")
        obj._set("label", "test-label")
        obj._set("_populated", True)

        result = obj._serialize()

        # The serialized output should use the original API attribute name
        self.assertIn("class", result)
        self.assertEqual(result["class"], "premium")
        self.assertEqual(result["label"], "test-label")
        # Should not contain the aliased name
        self.assertNotIn("service_class", result)

    def test_properties_with_alias(self):
        """Test that properties_with_alias returns correct mapping"""

        class TestModel(Base):
            api_endpoint = "/test/{id}"
            properties = {
                "id": Property(identifier=True),
                "service_class": Property(mutable=True, alias_of="class"),
                "beta_type": Property(alias_of="type"),
                "label": Property(mutable=True),
            }

        obj = TestModel(self.client, 123)

        alias_map = obj.properties_with_alias

        # Should contain mappings for aliased properties
        self.assertIn("class", alias_map)
        self.assertIn("type", alias_map)

        # Should map to tuples of (alias_name, Property)
        alias_name, prop = alias_map["class"]
        self.assertEqual(alias_name, "service_class")
        self.assertEqual(prop.alias_of, "class")

        alias_name, prop = alias_map["type"]
        self.assertEqual(alias_name, "beta_type")
        self.assertEqual(prop.alias_of, "type")

        # Non-aliased properties should not be in the map
        self.assertNotIn("label", alias_map)
        self.assertNotIn("id", alias_map)

    def test_alias_no_conflict_with_regular_properties(self):
        """Test that aliased properties don't conflict with regular properties"""

        class TestModel(Base):
            api_endpoint = "/test/{id}"
            properties = {
                "id": Property(identifier=True),
                "service_class": Property(mutable=True, alias_of="class"),
                "label": Property(mutable=True),
                "status": Property(),
            }

        json_data = {
            "id": 123,
            "class": "premium",
            "label": "test-label",
            "status": "active",
        }

        obj = TestModel(self.client, 123, json_data)

        # All properties should be set correctly
        self.assertEqual(obj.service_class, "premium")
        self.assertEqual(obj.label, "test-label")
        self.assertEqual(obj.status, "active")

    def test_multiple_aliases(self):
        """Test handling multiple aliased properties"""

        class TestModel(Base):
            api_endpoint = "/test/{id}"
            properties = {
                "id": Property(identifier=True),
                "service_class": Property(mutable=True, alias_of="class"),
                "beta_type": Property(mutable=True, alias_of="type"),
                "import_data": Property(mutable=True, alias_of="import"),
            }

        json_data = {
            "id": 123,
            "class": "premium",
            "type": "beta",
            "import": "data",
        }

        obj = TestModel(self.client, 123, json_data)

        # All aliased properties should be populated
        self.assertEqual(obj.service_class, "premium")
        self.assertEqual(obj.beta_type, "beta")
        self.assertEqual(obj.import_data, "data")

        # Serialization should use original names
        obj._set("_populated", True)
        result = obj._serialize()

        self.assertEqual(result["class"], "premium")
        self.assertEqual(result["type"], "beta")
        self.assertEqual(result["import"], "data")

    def test_alias_with_none_value(self):
        """Test that aliased properties handle None values correctly"""

        class TestModel(Base):
            api_endpoint = "/test/{id}"
            properties = {
                "id": Property(identifier=True),
                "service_class": Property(mutable=True, alias_of="class"),
            }

        json_data = {
            "id": 123,
            "class": None,
        }

        obj = TestModel(self.client, 123, json_data)

        # The aliased property should be None
        self.assertIsNone(obj.service_class)

    def test_alias_cached_property(self):
        """Test that properties_with_alias is cached"""

        class TestModel(Base):
            api_endpoint = "/test/{id}"
            properties = {
                "id": Property(identifier=True),
                "service_class": Property(alias_of="class"),
            }

        obj = TestModel(self.client, 123)

        # Access the cached property twice
        result1 = obj.properties_with_alias
        result2 = obj.properties_with_alias

        # Should return the same object (cached)
        self.assertIs(result1, result2)

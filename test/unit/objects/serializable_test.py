from dataclasses import dataclass
from test.unit.base import ClientBaseCase
from typing import Optional, Union

from linode_api4 import Base, ExplicitNullValue, JSONObject, Property


class JSONObjectTest(ClientBaseCase):
    def test_serialize_optional(self):
        @dataclass
        class Foo(JSONObject):
            always_include = {"foo"}

            foo: Optional[str] = None
            bar: Optional[str] = None
            baz: str = None
            foobar: Union[str, ExplicitNullValue, None] = None

        foo = Foo().dict

        assert foo["foo"] is None
        assert "bar" not in foo
        assert foo["baz"] is None
        assert "foobar" not in foo

        foo = Foo(foo="test", bar="test2", baz="test3", foobar="test4").dict

        assert foo["foo"] == "test"
        assert foo["bar"] == "test2"
        assert foo["baz"] == "test3"
        assert foo["foobar"] == "test4"

    def test_serialize_optional_include_None(self):
        @dataclass
        class Foo(JSONObject):
            include_none_values = True

            foo: Optional[str] = None
            bar: Optional[str] = None
            baz: str = None
            foobar: Union[str, ExplicitNullValue, None] = None

        foo = Foo().dict

        assert foo["foo"] is None
        assert foo["bar"] is None
        assert foo["baz"] is None
        assert foo["foobar"] is None

        foo = Foo(
            foo="test", bar="test2", baz="test3", foobar=ExplicitNullValue()
        ).dict

        assert foo["foo"] == "test"
        assert foo["bar"] == "test2"
        assert foo["baz"] == "test3"
        assert foo["foobar"] is None

    def test_serialize_put_class(self):
        """
        Ensures that the JSONObject put_class ClassVar functions as expected.
        """

        @dataclass
        class SubStructOptions(JSONObject):
            test1: Optional[str] = None

        @dataclass
        class SubStruct(JSONObject):
            put_class = SubStructOptions

            test1: str = ""
            test2: int = 0

        class Model(Base):
            api_endpoint = "/foo/bar"

            properties = {
                "id": Property(identifier=True),
                "substruct": Property(mutable=True, json_object=SubStruct),
            }

        mock_response = {
            "id": 123,
            "substruct": {
                "test1": "abc",
                "test2": 321,
            },
        }

        with self.mock_get(mock_response) as mock:
            obj = self.client.load(Model, 123)

            assert mock.called

        assert obj.id == 123
        assert obj.substruct.test1 == "abc"
        assert obj.substruct.test2 == 321

        obj.substruct.test1 = "cba"

        with self.mock_put(mock_response) as mock:
            obj.save()

            assert mock.called
            assert mock.call_data == {
                "substruct": {
                    "test1": "cba",
                }
            }

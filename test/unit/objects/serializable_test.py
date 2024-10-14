from dataclasses import dataclass
from test.unit.base import ClientBaseCase
from typing import Optional

from linode_api4 import JSONObject


class JSONObjectTest(ClientBaseCase):
    def test_serialize_optional(self):
        @dataclass
        class Foo(JSONObject):
            always_include = {"foo"}

            foo: Optional[str] = None
            bar: Optional[str] = None
            baz: str = None

        foo = Foo().dict

        assert foo["foo"] is None
        assert "bar" not in foo
        assert foo["baz"] is None

        foo = Foo(foo="test", bar="test2", baz="test3").dict

        assert foo["foo"] == "test"
        assert foo["bar"] == "test2"
        assert foo["baz"] == "test3"

    def test_serialize_optional_include_None(self):
        @dataclass
        class Foo(JSONObject):
            include_none_values = True

            foo: Optional[str] = None
            bar: Optional[str] = None
            baz: str = None

        foo = Foo().dict

        assert foo["foo"] is None
        assert foo["bar"] is None
        assert foo["baz"] is None

        foo = Foo(foo="test", bar="test2", baz="test3").dict

        assert foo["foo"] == "test"
        assert foo["bar"] == "test2"
        assert foo["baz"] == "test3"

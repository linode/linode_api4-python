import inspect
from dataclasses import dataclass, fields
from enum import Enum
from types import SimpleNamespace
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Set,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from linode_api4.objects.filtering import FilterableAttribute

# Wraps the SimpleNamespace class and allows for
# SQLAlchemy-style filter generation on JSONObjects.
JSONFilterGroup = SimpleNamespace


class JSONFilterableMetaclass(type):
    def __init__(cls, name, bases, dct):
        setattr(
            cls,
            "filters",
            JSONFilterGroup(
                **{
                    k: FilterableAttribute(k)
                    for k in cls.__annotations__.keys()
                }
            ),
        )

        super().__init__(name, bases, dct)


@dataclass
class JSONObject(metaclass=JSONFilterableMetaclass):
    """
    A simple helper class for serializable API objects.
    This is typically used for nested object values.

    This class act similarly to MappedObject but with explicit
    fields and static typing.
    """

    filters: ClassVar[JSONFilterGroup] = None
    """
    A group containing FilterableAttributes used to create SQLAlchemy-style filters.

    Example usage::
        self.client.regions.availability(
            RegionAvailabilityEntry.filters.plan == "premium4096.7"
        )
    """

    include_none_values: ClassVar[bool] = False
    """
    If true, all None values for this class will be explicitly included in 
    the serialized output for instance of this class.
    """

    always_include: ClassVar[Set[str]] = {}
    """
    A set of keys corresponding to fields that should always be
    included in the generated output regardless of whether their values
    are None.
    """

    put_class: ClassVar[Optional[Type["JSONObject"]]] = None
    """
    An alternative JSONObject class to use as the schema for PUT requests.
    This prevents read-only fields from being included in PUT request bodies,
    which in theory will result in validation errors from the API.
    """

    def __init__(self):
        raise NotImplementedError(
            "JSONObject is not intended to be constructed directly"
        )

    # TODO: Implement __repr__
    @staticmethod
    def _unwrap_type(field_type: type) -> type:
        args = get_args(field_type)
        origin_type = get_origin(field_type)

        # We don't want to try to unwrap Dict, List, Set, etc. values
        if origin_type is not Union:
            return field_type

        if len(args) == 0:
            raise TypeError("Expected type to have arguments, got none")

        # Use the first type in the Union's args
        return JSONObject._unwrap_type(args[0])

    @staticmethod
    def _try_from_json(json_value: Any, field_type: type):
        """
        Determines whether a JSON dict is an instance of a field type.
        """

        field_type = JSONObject._unwrap_type(field_type)

        if inspect.isclass(field_type) and issubclass(field_type, JSONObject):
            return field_type.from_json(json_value)

        return json_value

    @classmethod
    def _parse_attr_list(cls, json_value: Any, field_type: type):
        """
        Attempts to parse a list attribute with a given value and field type.
        """

        # Edge case for optional list values
        if json_value is None:
            return None

        type_hint_args = get_args(field_type)

        if len(type_hint_args) < 1:
            return cls._try_from_json(json_value, field_type)

        return [
            cls._try_from_json(item, type_hint_args[0]) for item in json_value
        ]

    @classmethod
    def _parse_attr(cls, json_value: Any, field_type: type):
        """
        Attempts to parse an attribute with a given value and field type.
        """

        field_type = JSONObject._unwrap_type(field_type)

        if list in (field_type, get_origin(field_type)):
            return cls._parse_attr_list(json_value, field_type)

        return cls._try_from_json(json_value, field_type)

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> Optional["JSONObject"]:
        """
        Creates an instance of this class from a JSON dict, respecting json_key metadata.
        """
        if json is None:
            return None

        obj = cls()

        type_hints = get_type_hints(cls)

        for f in fields(cls):
            json_key = f.metadata.get("json_key", f.name)
            field_type = type_hints.get(f.name)
            value = json.get(json_key)
            parsed_value = cls._parse_attr(value, field_type)
            setattr(obj, f.name, parsed_value)

        return obj

    def _serialize(self, is_put: bool = False) -> Dict[str, Any]:
        """
        Serializes this object into a JSON dict.
        """
        cls = type(self)

        if is_put and cls.put_class is not None:
            cls = cls.put_class

        cls_field_keys = {field.name for field in fields(cls)}

        type_hints = get_type_hints(cls)

        def attempt_serialize(value: Any) -> Any:
            """
            Attempts to serialize the given value, else returns the value unchanged.
            """
            if issubclass(type(value), JSONObject):
                return value._serialize(is_put=is_put)

            # Needed to avoid circular imports without a breaking change
            from linode_api4.objects.base import (  # pylint: disable=import-outside-toplevel
                ExplicitNullValue,
            )

            if value == ExplicitNullValue or isinstance(
                value, ExplicitNullValue
            ):
                return None

            return value

        def should_include(key: str, value: Any) -> bool:
            """
            Returns whether the given key/value pair should be included in the resulting dict.
            """

            # During PUT operations, keys not present in the put_class should be excluded
            if key not in cls_field_keys:
                return False

            if cls.include_none_values or key in cls.always_include:
                return True

            hint = type_hints.get(key)

            # We want to exclude any Optional values that are None
            # NOTE: We need to check for Union here because Optional is an alias of Union.
            if (
                hint is None
                or get_origin(hint) is not Union
                or type(None) not in get_args(hint)
            ):
                return True

            return value is not None

        result = {}

        for f in fields(self):
            k = f.name
            json_key = f.metadata.get("json_key", k)
            v = getattr(self, k)

            if not should_include(k, v):
                continue

            if isinstance(v, List):
                v = [attempt_serialize(j) for j in v]
            elif isinstance(v, Dict):
                v = {k: attempt_serialize(j) for k, j in v.items()}
            else:
                v = attempt_serialize(v)

            result[json_key] = v

        return result

    @property
    def dict(self) -> Dict[str, Any]:
        """
        Alias for JSONObject._serialize()
        """
        return self._serialize()

    # Various dict methods for backwards compat
    def __getitem__(self, key) -> Any:
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __iter__(self) -> Any:
        return vars(self)

    def __delitem__(self, key):
        setattr(self, key, None)

    def __len__(self):
        return len(vars(self))


class StrEnum(str, Enum):
    """
    Used for enums that are of type string, which is necessary
    for implicit JSON serialization.

    NOTE: Replace this with StrEnum once Python 3.10 has been EOL'd.
    See: https://docs.python.org/3/library/enum.html#enum.StrEnum
    """

    def __new__(cls, *values):
        value = str(*values)
        member = str.__new__(cls, value)
        member._value_ = value
        return member

    def __str__(self):
        return self._value_

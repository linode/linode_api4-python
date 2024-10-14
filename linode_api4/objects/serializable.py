import inspect
from dataclasses import dataclass
from enum import Enum
from types import SimpleNamespace
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Set,
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
        Creates an instance of this class from a JSON dict.
        """
        if json is None:
            return None

        obj = cls()

        type_hints = get_type_hints(cls)

        for k in vars(obj):
            setattr(obj, k, cls._parse_attr(json.get(k), type_hints.get(k)))

        return obj

    def _serialize(self) -> Dict[str, Any]:
        """
        Serializes this object into a JSON dict.
        """
        cls = type(self)
        type_hints = get_type_hints(cls)

        def attempt_serialize(value: Any) -> Any:
            """
            Attempts to serialize the given value, else returns the value unchanged.
            """
            if issubclass(type(value), JSONObject):
                return value._serialize()

            return value

        def should_include(key: str, value: Any) -> bool:
            """
            Returns whether the given key/value pair should be included in the resulting dict.
            """

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

        for k, v in vars(self).items():
            if not should_include(k, v):
                continue

            if isinstance(v, List):
                v = [attempt_serialize(j) for j in v]
            elif isinstance(v, Dict):
                v = {k: attempt_serialize(j) for k, j in v.items()}
            else:
                v = attempt_serialize(v)

            result[k] = v

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

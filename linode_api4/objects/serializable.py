import inspect
from dataclasses import asdict, dataclass
from types import SimpleNamespace
from typing import (
    Any,
    ClassVar,
    Dict,
    Optional,
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

    def __init__(self):
        raise NotImplementedError(
            "JSONObject is not intended to be constructed directly"
        )

    # TODO: Implement __repr__

    @staticmethod
    def _try_from_json(json_value: Any, field_type: type):
        """
        Determines whether a JSON dict is an instance of a field type.
        """
        if inspect.isclass(field_type) and issubclass(field_type, JSONObject):
            return field_type.from_json(json_value)
        return json_value

    @classmethod
    def _parse_attr_list(cls, json_value, field_type):
        """
        Attempts to parse a list attribute with a given value and field type.
        """

        type_hint_args = get_args(field_type)

        if len(type_hint_args) < 1:
            return cls._try_from_json(json_value, field_type)

        return [
            cls._try_from_json(item, type_hint_args[0]) for item in json_value
        ]

    @classmethod
    def _parse_attr(cls, json_value, field_type):
        """
        Attempts to parse an attribute with a given value and field type.
        """

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
        return asdict(self)

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

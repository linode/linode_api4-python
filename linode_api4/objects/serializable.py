import inspect
from dataclasses import asdict, dataclass
from typing import Any, Dict, get_type_hints


@dataclass
class JSONObject:
    """
    A simple helper class for serializable API objects.
    This is typically used for nested object values.

    This class act similarly to MappedObject but with explicit
    fields and static typing.
    """

    def __init__(self):
        raise NotImplementedError(
            "JSONObject is not intended to be constructed directly"
        )

    # TODO: Implement __repr__

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> "JSONObject":
        """
        Creates an instance of this class from a JSON dict.
        """
        obj = cls()

        type_hints = get_type_hints(cls)

        for k in vars(obj):
            json_value = json.get(k)
            field_type = type_hints.get(k)

            if json_value is None:
                continue

            if (
                field_type is not None
                and inspect.isclass(field_type)
                and issubclass(field_type, JSONObject)
            ):
                setattr(obj, k, field_type.from_json(json_value))
                continue

            setattr(obj, k, json_value)

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

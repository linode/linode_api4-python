"""
Contains various utility functions.
"""
from typing import Any, Dict


def drop_null_keys(data: Dict[Any, Any], recursive=True) -> Dict[Any, Any]:
    """
    Traverses a dict and drops any keys that map to None values.
    """

    if not recursive:
        return {k: v for k, v in data.items() if v is not None}

    def recursive_helper(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                k: recursive_helper(v)
                for k, v in value.items()
                if v is not None
            }

        if isinstance(value, list):
            return [recursive_helper(v) for v in value]

        return value

    return recursive_helper(data)

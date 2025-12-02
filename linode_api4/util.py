"""
Contains various utility functions.
"""

from typing import Any, Dict
import string


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


def generate_device_suffixes(n):
    """
    Generate n alphabetical suffixes starting with a, b, c, etc.
    After z, continue with aa, ab, ac, etc. followed by aaa, aab, etc.
    Example:
        generate_device_suffixes(30) ->
        ['a', 'b', 'c', ..., 'z', 'aa', 'ab', 'ac', 'ad']
    """
    letters = string.ascii_lowercase
    result = []
    i = 0

    while len(result) < n:
        s = ""
        x = i
        while True:
            s = letters[x % 26] + s
            x = x // 26 - 1
            if x < 0:
                break
        result.append(s)
        i += 1
    return result

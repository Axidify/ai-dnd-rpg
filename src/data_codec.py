"""
Generic conversion between dataclasses and plain data (dicts/lists/scalars).

Used to keep scenario content (locations, scenes, NPCs, quests, shops) in
data files instead of Python constructors. ``to_data`` omits fields still at
their default value so the files stay short; ``from_data`` rebuilds objects
from type hints, so any dataclass made of str/int/float/bool, Enums, lists,
dicts and nested dataclasses round-trips without per-class code.
"""

import copy
import dataclasses
import enum
import typing
from functools import lru_cache
from typing import Any, Dict, Union


def _default_of(f: dataclasses.Field) -> Any:
    if f.default is not dataclasses.MISSING:
        return f.default
    if f.default_factory is not dataclasses.MISSING:  # type: ignore[misc]
        return f.default_factory()  # type: ignore[misc]
    return dataclasses.MISSING


def to_data(obj: Any) -> Any:
    """Convert a dataclass (recursively) to plain data, omitting default-valued fields."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        out: Dict[str, Any] = {}
        for f in dataclasses.fields(obj):
            if not f.init:
                continue
            value = getattr(obj, f.name)
            if value == _default_of(f):
                continue
            out[f.name] = to_data(value)
        return out
    if isinstance(obj, enum.Enum):
        # String-valued enums use their value ("tavern"); auto()/int enums use
        # their name ("MAIN") so data files stay readable.
        return obj.value if isinstance(obj.value, str) else obj.name
    if isinstance(obj, dict):
        return {str(k): to_data(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_data(v) for v in obj]
    if isinstance(obj, (set, frozenset)):
        return sorted(to_data(v) for v in obj)
    return obj


@lru_cache(maxsize=None)
def _hints(cls: type) -> Dict[str, Any]:
    return typing.get_type_hints(cls)


def from_data(tp: Any, data: Any) -> Any:
    """Build a value of type ``tp`` from plain data."""
    if data is None:
        return None
    if tp is Any:
        return copy.deepcopy(data)

    origin = typing.get_origin(tp)
    args = typing.get_args(tp)

    if origin is Union:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return from_data(non_none[0], data)
        return data
    if origin in (list, typing.List):
        (item_tp,) = args or (Any,)
        return [from_data(item_tp, v) for v in data]
    if origin in (set, frozenset):
        (item_tp,) = args or (Any,)
        return origin(from_data(item_tp, v) for v in data)
    if origin is tuple:
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(from_data(args[0], v) for v in data)
        return tuple(from_data(a, v) for a, v in zip(args, data))
    if origin in (dict, typing.Dict):
        key_tp, val_tp = args or (Any, Any)
        return {from_data(key_tp, k): from_data(val_tp, v) for k, v in data.items()}

    if isinstance(tp, type) and issubclass(tp, enum.Enum):
        if isinstance(data, str) and data in tp.__members__:
            return tp[data]
        return tp(data)
    if dataclasses.is_dataclass(tp):
        hints = _hints(tp)
        known = {f.name for f in dataclasses.fields(tp) if f.init}
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"{tp.__name__}: unknown field(s) {sorted(unknown)}")
        return tp(**{name: from_data(hints[name], value) for name, value in data.items()})
    if tp is float and isinstance(data, int):
        return float(data)
    if isinstance(data, (dict, list)):
        # Untyped containers (bare dict/list/Any): never share the caller's data
        return copy.deepcopy(data)
    return data

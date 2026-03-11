import dataclasses
import typing
from collections.abc import Callable
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel


def is_serdecompat(a: object, b: object) -> bool:
    """Check if values of type ``a`` can be serialized into a representation compatible with type ``b``.

    The function checks *serialization compatibility* rather than
    runtime subtype relationships. In other words, it answers the question:

        "If a value of type A is serialized, could it be deserialized as B?"

    Compatibility is structural and recursive.

    The following rules apply:

    - Primitive widening is supported (e.g. ``bool -> int``, ``int -> float``).
    - ``Union`` types are handled covariantly:
        - ``Union[A, B] -> T`` if both ``A -> T`` and ``B -> T``.
        - ``T -> Union[A, B]`` if ``T -> A`` or ``T -> B``.
    - Generic containers are checked element-wise (e.g. ``list[bool] -> list[int]``).
    - Tuple compatibility supports both fixed and variadic tuples (``tuple[T, ...]``).
    - Compatibility across schema types is allowed if their fields match structurally.
      The following types are supported:
        - dataclasses
        - ``TypedDict``
        - ``pydantic.BaseModel`` subclasses
    - ``Literal`` types are compatible with the type of their values.
    - ``Annotated`` wrappers are ignored.

    Extra fields in the source type are allowed as long as
    all fields required by the target type exist and are compatible.

    Examples:
        >>> is_serdecompat(bool, int)
        True

        >>> is_serdecompat(list[bool], list[int])
        True

        >>> is_serdecompat(tuple[bool, ...], tuple[int, ...])
        True

        >>> @dataclasses.dataclass
        ... class A:
        ...     x: bool
        ...     y: int
        >>> class B(pydantic.BaseModel):
        ...     x: int
        >>> is_serdecompat(A, B)
        True

    Returns:
        True if serialized representations of ``a`` are compatible with ``b``.
    """
    a = _normalize(a)
    b = _normalize(b)

    if b is Any:
        return True

    if _is_simply_serdecompat(a, b):
        return True

    if a == b:
        return True

    for handler in _SERDECOMPAT_HANDLERS:
        result = handler(a, b)
        if result is not None:
            return result

    args_a = typing.get_args(a)
    args_b = typing.get_args(b)

    if _is_union(a):
        return all(is_serdecompat(x, b) for x in args_a)

    if _is_union(b):
        return any(is_serdecompat(a, x) for x in args_b)

    origin_a = typing.get_origin(a)
    origin_b = typing.get_origin(b)

    if origin_a and origin_b and origin_a == origin_b:
        if len(args_a) != len(args_b):
            return False
        return all(is_serdecompat(x, y) for x, y in zip(args_a, args_b, strict=True))

    return False


def _normalize(tp: Any) -> Any:
    origin = typing.get_origin(tp)
    if origin is Annotated:
        return typing.get_args(tp)[0]
    return tp


def _is_simply_serdecompat(a: object, b: object) -> bool:
    return (
        (a is bool and b is bool)
        or (a is bool and b is float)
        or (a is int and b is float)
        or (a is str and b is bytes)
    )


def _is_union(tp: Any) -> bool:
    return typing.get_origin(tp) is Union


def _handle_literal(a: object, b: object) -> bool | None:
    if _is_literal(a):
        return _is_literal_serdecompat(a, b)

    if _is_literal(b):
        return _is_serdecompat_literal(a, b)


def _is_literal(tp: Any) -> bool:
    return typing.get_origin(tp) is Literal


def _is_literal_serdecompat(a: object, b: object) -> bool:
    values = typing.get_args(a)
    return all(is_serdecompat(type(v), b) for v in values)


def _is_serdecompat_literal(a: object, b: object) -> bool:
    values = typing.get_args(b)
    return all(is_serdecompat(a, type(v)) for v in values)


def _handle_tuple(a: object, b: object) -> bool | None:
    origin_a = typing.get_origin(a)
    origin_b = typing.get_origin(b)

    if origin_a is not tuple or origin_b is not tuple:
        return None

    args_a = typing.get_args(a)
    args_b = typing.get_args(b)

    if (
        len(args_a) == 2
        and args_a[1] is Ellipsis
        and len(args_b) == 2
        and args_b[1] is Ellipsis
    ):
        return is_serdecompat(args_a[0], args_b[0])

    if len(args_a) == 2 and args_a[1] is Ellipsis:
        return all(is_serdecompat(args_a[0], t) for t in args_b)

    if len(args_b) == 2 and args_b[1] is Ellipsis:
        return all(is_serdecompat(t, args_b[0]) for t in args_a)

    if len(args_a) != len(args_b):
        return False

    return all(is_serdecompat(x, y) for x, y in zip(args_a, args_b, strict=True))


def _handle_sub_class(a: object, b: object) -> bool | None:
    if isinstance(a, type) and isinstance(b, type) and issubclass(a, b):
        return True
    return None


def _handle_abc_container(a: object, b: object) -> bool | None:
    origin_a = typing.get_origin(a)
    origin_b = typing.get_origin(b)

    if not origin_a or not origin_b:
        return None

    if not isinstance(origin_a, type) or not isinstance(origin_b, type):
        return None

    if not issubclass(origin_a, origin_b):
        return None

    args_a = typing.get_args(a)
    args_b = typing.get_args(b)

    if not args_b:
        return True

    if len(args_a) != len(args_b):
        return False

    return all(is_serdecompat(x, y) for x, y in zip(args_a, args_b, strict=True))


def _handle_schema_to_schema(a: object, b: object) -> bool | None:
    fields_a = _get_schema_fields(a)
    fields_b = _get_schema_fields(b)

    if fields_a is None or fields_b is None:
        return None

    for name, type_b in fields_b.items():
        if name not in fields_a:
            return False

        type_a = fields_a[name]

        if not is_serdecompat(type_a, type_b):
            return False

    return True


def _get_schema_fields(tp: object) -> dict[str, object] | None:
    if tp_dc := _is_dataclass_type(tp):
        return {field.name: field.type for field in dataclasses.fields(tp_dc)}

    if tp_model := _is_pydantic_model(tp):
        return {name: field.annotation for name, field in tp_model.model_fields.items()}

    if _is_typed_dict(tp):
        return typing.get_type_hints(tp)

    return None


def _is_dataclass_type(tp: object) -> type | None:
    if isinstance(tp, type) and dataclasses.is_dataclass(tp):
        return tp
    return None


def _is_typed_dict(tp: object) -> type | None:
    if isinstance(tp, type) and typing.is_typeddict(tp):
        return tp
    return None


def _is_pydantic_model(tp: object) -> type[BaseModel] | None:
    if isinstance(tp, type) and issubclass(tp, BaseModel):
        return tp
    return None


_SERDECOMPAT_HANDLERS: list[Callable[[object, object], bool | None]] = [
    _handle_literal,
    _handle_schema_to_schema,
    _handle_sub_class,
    _handle_tuple,
    _handle_abc_container,
]

import dataclasses
import typing
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import (
    Annotated,
    Any,
    Literal,
    TypedDict,
    Union,
)

from pydantic import BaseModel

# TODO:
# - check if TypeAlias break things
# - NewType
# - Field defaults / optional fields:
#     @dataclass
#     class B:
#         x: int
#         y: int = 0
#   then A(x:int) -> B should be allowed.


def is_serdecompat(a: object, b: object) -> bool:
    a = normalize(a)
    b = normalize(b)

    # Any accepts everything
    if b is Any:
        return True

    # direct rule
    if is_simply_serdecompat(a, b):
        return True

    # identical
    if a == b:
        return True

    # Literal -> B
    if is_literal(a):
        return is_literal_serdecompat(a, b)

    # A -> Literal
    if is_literal(b):
        return is_serdecompat_literal(a, b)

    for handler in SERDEABLE_HANDLERS:
        result = handler(a, b)
        if result is not None:
            return result

    args_a = typing.get_args(a)
    args_b = typing.get_args(b)

    # Union -> B
    if is_union(a):
        return all(is_serdecompat(x, b) for x in args_a)

    # A -> Union
    if is_union(b):
        return any(is_serdecompat(a, x) for x in args_b)

    origin_a = typing.get_origin(a)
    origin_b = typing.get_origin(b)

    # generic containers
    if origin_a and origin_b and origin_a == origin_b:
        if len(args_a) != len(args_b):
            return False
        return all(is_serdecompat(x, y) for x, y in zip(args_a, args_b, strict=True))

    return False


def normalize(tp: Any) -> Any:
    """Remove Annotated wrappers."""
    origin = typing.get_origin(tp)
    if origin is Annotated:
        return typing.get_args(tp)[0]
    return tp


def is_simply_serdecompat(a: object, b: object) -> bool:
    return (
        (a is bool and b is bool)
        or (a is bool and b is float)
        or (a is int and b is float)
        or (a is str and b is bytes)
    )


def is_union(tp: Any) -> bool:
    return typing.get_origin(tp) is Union


def is_literal(tp: Any) -> bool:
    return typing.get_origin(tp) is Literal


# literal -> type
def is_literal_serdecompat(a: object, b: object) -> bool:
    values = typing.get_args(a)
    return all(is_serdecompat(type(v), b) for v in values)


# literal -> type
def is_serdecompat_literal(a: object, b: object) -> bool:
    values = typing.get_args(b)
    return all(is_serdecompat(a, type(v)) for v in values)


def handle_tuple(a: object, b: object) -> bool | None:
    origin_a = typing.get_origin(a)
    origin_b = typing.get_origin(b)

    if origin_a is not tuple or origin_b is not tuple:
        return None

    args_a = typing.get_args(a)
    args_b = typing.get_args(b)

    # tuple[T, ...] -> tuple[U, ...]
    if (
        len(args_a) == 2
        and args_a[1] is Ellipsis
        and len(args_b) == 2
        and args_b[1] is Ellipsis
    ):
        return is_serdecompat(args_a[0], args_b[0])

    # tuple[T, ...] -> tuple[U1, U2, ..., UN]
    if len(args_a) == 2 and args_a[1] is Ellipsis:
        return all(is_serdecompat(args_a[0], t) for t in args_b)

    # tuple[T1, T2, ..., TN] -> tuple[U, ...]
    if len(args_b) == 2 and args_b[1] is Ellipsis:
        return all(is_serdecompat(t, args_b[0]) for t in args_a)

    # fixed tuple -> fixed tuple
    if len(args_a) != len(args_b):
        return False

    return all(is_serdecompat(x, y) for x, y in zip(args_a, args_b, strict=True))

    return None


def handle_sub_class(a: object, b: object) -> bool | None:
    if isinstance(a, type) and isinstance(b, type) and issubclass(a, b):
        return True


def handle_abc_container(a: object, b: object) -> bool | None:
    origin_a = typing.get_origin(a)
    origin_b = typing.get_origin(b)

    if not origin_a or not origin_b:
        return None

    if not isinstance(origin_a, type) or not isinstance(origin_b, type):
        return None

    # allow list -> Sequence, dict -> Mapping, etc
    if not issubclass(origin_a, origin_b):
        return None

    args_a = typing.get_args(a)
    args_b = typing.get_args(b)

    if not args_b:
        return True

    if len(args_a) != len(args_b):
        return False

    return all(is_serdecompat(x, y) for x, y in zip(args_a, args_b, strict=True))


def handle_schema_to_schema(a: object, b: object) -> bool | None:
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
    # dataclass
    if tp_dc := _is_dataclass_type(tp):
        return {f.name: f.type for f in dataclasses.fields(tp_dc)}

    # pydantic
    if tp_model := _is_pydantic_model(tp):
        return {name: f.annotation for name, f in tp_model.model_fields.items()}

    # typed dict
    if _is_typed_dict(tp):
        return typing.get_type_hints(tp)

    return None


# NOTE: dataclasses are not special types like BaseModel
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


SERDEABLE_HANDLERS: list[Callable[[object, object], bool | None]] = [
    handle_schema_to_schema,
    handle_sub_class,
    handle_tuple,
    handle_abc_container,
]


def main() -> None:
    print(f"{is_serdecompat(bool, int) = }")
    print(f"{is_serdecompat(list[bool], list[int]) = }")
    print(f"{is_serdecompat(list[bool | int], list[int]) = }")
    print(f"{is_serdecompat(dict[bool | int, float], dict[float, float]) = }")

    test_optional()
    test_literal()
    test_tuple()
    test_dataclasses()
    test_typed_dict()
    test_pydantic_models()
    test_abc_containers()
    test_schema_to_schema()


def test_optional() -> None:
    print(f"{is_serdecompat(bool, int | None) = }")
    print(f"{is_serdecompat(type(None), int | None) = }")
    print(f"{is_serdecompat(type(None), int) = }")
    print(f"{is_serdecompat(int | None, int) = }")


def test_literal() -> None:
    print(f"{is_serdecompat(Literal[1], int) = }")
    print(f"{is_serdecompat(Literal[1, 2], int) = }")
    print(f"{is_serdecompat(Literal["a"], str) = }")
    print(f"{is_serdecompat(Literal[True], int) = }")
    print(f"{is_serdecompat(list[Literal[1,2]], list[int]) = }")
    print(f"{is_serdecompat(tuple[Literal[1], ...], tuple[int, ...]) = }")
    print(f"{is_serdecompat(dict[str, Literal[1]], dict[str, int]) = }")


def test_tuple() -> None:
    print(f"{is_serdecompat(tuple[bool, ...], tuple[int, ...]) = }")
    print(f"{is_serdecompat(tuple[bool, bool], tuple[int, ...]) = }")
    print(f"{is_serdecompat(tuple[bool, ...], tuple[int, float]) = }")
    print(f"{is_serdecompat(tuple[list[bool], ...], tuple[list[int], ...]) = }")


def test_dataclasses() -> None:
    @dataclasses.dataclass
    class A:
        x: bool
        y: int
        z: str
        values: list[bool]

    @dataclasses.dataclass
    class B:
        x: int
        y: float
        values: list[int]

    print(f"{is_serdecompat(A, B) = }")

    @dataclasses.dataclass
    class C:
        x: list[A]
        y: dict[str, A]
        z: tuple[int, A]

    @dataclasses.dataclass
    class D:
        x: list[B]
        y: dict[bytes, B]
        z: tuple[float, A]

    print(f"{is_serdecompat(C, D) = }")


def test_typed_dict() -> None:
    class A(TypedDict):
        x: bool
        y: int
        values: list[bool]

    class B(TypedDict):
        x: int
        y: float
        values: list[int]

    print(f"{is_serdecompat(A, B) = }")

    class C(TypedDict):
        x: list[A]
        y: dict[str, A]

    class D(TypedDict):
        x: list[B]
        y: dict[bytes, B]

    print(f"{is_serdecompat(C, D) = }")


def test_pydantic_models() -> None:
    class A(BaseModel):
        x: bool
        y: int
        z: str
        values: list[bool]

    class B(BaseModel):
        x: int
        y: float
        values: list[int]

    print(f"{is_serdecompat(A, B) = }")

    class C(BaseModel):
        x: list[A]
        y: dict[str, A]
        z: tuple[int, A]

    class D(BaseModel):
        x: list[B]
        y: dict[bytes, B]
        z: tuple[float, A]

    print(f"{is_serdecompat(C, D) = }")


def test_schema_to_schema() -> None:
    class A(BaseModel):
        x: bool
        y: int
        z: str
        values: list[bool]

    @dataclasses.dataclass
    class B:
        x: int
        y: float
        values: list[int]

    print(f"{is_serdecompat(A, B) = }")


def test_abc_containers() -> None:
    print(f"{is_serdecompat(list[bool], Sequence[int]) = }")
    print(f"{is_serdecompat(list[int], Sequence[bool]) = }")
    print(f"{is_serdecompat(set[bool], Iterable[int]) = }")
    print(f"{is_serdecompat(dict[str, bool], Mapping[str, int]) = }")
    print(f"{is_serdecompat(dict[bytes, bool], Mapping[str, int]) = }")


if __name__ == "__main__":
    main()

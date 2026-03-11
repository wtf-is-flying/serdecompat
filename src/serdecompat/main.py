import dataclasses
from collections.abc import Iterable, Mapping, Sequence
from typing import Literal, TypedDict

from pydantic import BaseModel

from serdecompat import is_serdecompat


def main() -> None:
    print(f"{is_serdecompat(bool, int) = }")
    print(f"{is_serdecompat(list[bool], list[int]) = }")
    print(f"{is_serdecompat(list[bool | int], list[int]) = }")
    print(f"{is_serdecompat(dict[bool | int, float], dict[float, float]) = }")

    _print_optional_examples()
    _print_literal_examples()
    _print_tuple_examples()
    _print_dataclass_examples()
    _print_typed_dict_examples()
    _print_pydantic_examples()
    _print_abc_container_examples()
    _print_schema_to_schema_examples()


def _print_optional_examples() -> None:
    print(f"{is_serdecompat(bool, int | None) = }")
    print(f"{is_serdecompat(type(None), int | None) = }")
    print(f"{is_serdecompat(type(None), int) = }")
    print(f"{is_serdecompat(int | None, int) = }")


def _print_literal_examples() -> None:
    print(f"{is_serdecompat(Literal[1], int) = }")
    print(f"{is_serdecompat(Literal[1, 2], int) = }")
    print(f"{is_serdecompat(Literal['a'], str) = }")
    print(f"{is_serdecompat(Literal[True], int) = }")
    print(f"{is_serdecompat(list[Literal[1, 2]], list[int]) = }")
    print(f"{is_serdecompat(tuple[Literal[1], ...], tuple[int, ...]) = }")
    print(f"{is_serdecompat(dict[str, Literal[1]], dict[str, int]) = }")


def _print_tuple_examples() -> None:
    print(f"{is_serdecompat(tuple[bool, ...], tuple[int, ...]) = }")
    print(f"{is_serdecompat(tuple[bool, bool], tuple[int, ...]) = }")
    print(f"{is_serdecompat(tuple[bool, ...], tuple[int, float]) = }")
    print(f"{is_serdecompat(tuple[list[bool], ...], tuple[list[int], ...]) = }")


def _print_dataclass_examples() -> None:
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


def _print_typed_dict_examples() -> None:
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


def _print_pydantic_examples() -> None:
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


def _print_schema_to_schema_examples() -> None:
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


def _print_abc_container_examples() -> None:
    print(f"{is_serdecompat(list[bool], Sequence[int]) = }")
    print(f"{is_serdecompat(list[int], Sequence[bool]) = }")
    print(f"{is_serdecompat(set[bool], Iterable[int]) = }")
    print(f"{is_serdecompat(dict[str, bool], Mapping[str, int]) = }")
    print(f"{is_serdecompat(dict[bytes, bool], Mapping[str, int]) = }")


if __name__ == "__main__":
    main()

import dataclasses
from typing import TypedDict

from pydantic import BaseModel

from serdecompat import is_serdecompat


@dataclasses.dataclass
class DataclassA:
    x: bool
    y: int
    z: str
    values: list[bool]


@dataclasses.dataclass
class DataclassB:
    x: int
    y: float
    values: list[int]


@dataclasses.dataclass
class DataclassC:
    x: list[DataclassA]
    y: dict[str, DataclassA]
    z: tuple[int, DataclassA]


@dataclasses.dataclass
class DataclassD:
    x: list[DataclassB]
    y: dict[bytes, DataclassB]
    z: tuple[float, DataclassA]


class TypedDictA(TypedDict):
    x: bool
    y: int
    values: list[bool]


class TypedDictB(TypedDict):
    x: int
    y: float
    values: list[int]


class TypedDictC(TypedDict):
    x: list[TypedDictA]
    y: dict[str, TypedDictA]


class TypedDictD(TypedDict):
    x: list[TypedDictB]
    y: dict[bytes, TypedDictB]


class ModelA(BaseModel):
    x: bool
    y: int
    z: str
    values: list[bool]


class ModelB(BaseModel):
    x: int
    y: float
    values: list[int]


class ModelC(BaseModel):
    x: list[ModelA]
    y: dict[str, ModelA]
    z: tuple[int, ModelA]


class ModelD(BaseModel):
    x: list[ModelB]
    y: dict[bytes, ModelB]
    z: tuple[float, ModelA]


def test_dataclass_schema_cases() -> None:
    assert is_serdecompat(DataclassA, DataclassB) is True
    assert is_serdecompat(DataclassC, DataclassD) is True


def test_typed_dict_schema_cases() -> None:
    assert is_serdecompat(TypedDictA, TypedDictB) is True
    assert is_serdecompat(TypedDictC, TypedDictD) is True


def test_pydantic_schema_cases() -> None:
    assert is_serdecompat(ModelA, ModelB) is True
    assert is_serdecompat(ModelC, ModelD) is True


def test_cross_schema_case() -> None:
    assert is_serdecompat(ModelA, DataclassB) is True

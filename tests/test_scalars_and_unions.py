from typing import Annotated

import pytest

from serdecompat import is_serdecompat


@pytest.mark.parametrize(
    ("source", "target", "expected"),
    [
        (bool, int, True),
        (bool, int | None, True),
        (type(None), int | None, True),
        (type(None), int, False),
        (int | None, int, False),
        (Annotated[int, "metadata"], int, True),
        (list[bool], list[int], True),
        (list[bool | int], list[int], True),
        (dict[bool | int, float], dict[float, float], True),
    ],
)
def test_scalar_and_union_cases(source: object, target: object, expected: bool) -> None:
    assert is_serdecompat(source, target) is expected

from typing import Literal

import pytest

from serdecompat import is_serdecompat


@pytest.mark.parametrize(
    ("source", "target", "expected"),
    [
        (Literal[1], int, True),
        (Literal[1, 2], int, True),
        (Literal["a"], str, True),
        (Literal[True], int, True),
        (list[Literal[1, 2]], list[int], True),
        (tuple[Literal[1], ...], tuple[int, ...], True),
        (dict[str, Literal[1]], dict[str, int], True),
    ],
)
def test_literal_cases(source: object, target: object, expected: bool) -> None:
    assert is_serdecompat(source, target) is expected

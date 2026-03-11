from collections.abc import Iterable, Mapping, Sequence

import pytest

from serdecompat import is_serdecompat


@pytest.mark.parametrize(
    ("source", "target", "expected"),
    [
        (list[bool], Sequence[int], True),
        (list[int], Sequence[bool], False),
        (set[bool], Iterable[int], True),
        (dict[str, bool], Mapping[str, int], True),
        (dict[bytes, bool], Mapping[str, int], False),
    ],
)
def test_abc_container_cases(source: object, target: object, expected: bool) -> None:
    assert is_serdecompat(source, target) is expected

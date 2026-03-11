import pytest

from serdecompat import is_serdecompat


@pytest.mark.parametrize(
    ("source", "target", "expected"),
    [
        (tuple[bool, ...], tuple[int, ...], True),
        (tuple[bool, bool], tuple[int, ...], True),
        (tuple[bool, ...], tuple[int, float], True),
        (tuple[list[bool], ...], tuple[list[int], ...], True),
    ],
)
def test_tuple_cases(source: object, target: object, expected: bool) -> None:
    assert is_serdecompat(source, target) is expected

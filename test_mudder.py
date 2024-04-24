from collections.abc import Iterable
from itertools import tee

import pytest

from mudder import SymbolTable, alphabet, base36, base62, decimal


# from itertools docs
def pairwise(iterable: Iterable[str]) -> Iterable[tuple[str, str]]:
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b, strict=False)


@pytest.fixture
def hex_() -> SymbolTable:
    return SymbolTable("0123456789abcdef")


def test_reasonable_values() -> None:
    res = decimal.mudder("1", "2")
    assert res[0] == "15"


def test_reversing_start_end_reverses_outputs__controlled_cases() -> None:
    for num in range(1, 13):
        fwd = decimal.mudder("1", "2", num)
        rev = decimal.mudder("2", "1", num)
        assert "".join(fwd) == "".join(reversed(rev)), f"fwd = rev, {num}"
        assert all(a < b for a, b in pairwise(fwd)), "fwd all increasing"
        assert all(a > b for a, b in pairwise(rev)), "rev all decreasing"


def test_constructor_with_objects_and_maps() -> None:
    arr = ["_", "I", "II", "III", "IV", "V"]
    map_ = {
        "_": 0,
        "I": 1,
        "i": 1,
        "II": 2,
        "ii": 2,
        "III": 3,
        "iii": 3,
        "IV": 4,
        "iv": 4,
        "V": 5,
        "v": 5,
    }
    roman = SymbolTable(arr, map_)
    # not testing the same thing as mudderjs, but it's not applicable anyway
    assert roman.mudder(["I"], ["II"], 10) == roman.mudder(["i"], ["ii"], 10)


def test_matches_parseint_and_tostring(hex_: SymbolTable) -> None:
    # no built-in way to convert an int to base36, we'll use base 16 instead
    assert "0x" + hex_.number_to_string(123) == hex(123)
    assert hex_.string_to_number("7b") == int("7b", 16)


def test_fixes_1__repeated_recursive_subdivision() -> None:
    right = "z"
    for _i in range(50):
        newr = alphabet.mudder("a", right)[0]
        assert newr != "a"
        assert newr != right
        right = newr


def test_fixes_2__throws_when_fed_lexicographically_adjacent_strings() -> None:
    for i in range(2, 10):
        with pytest.raises(
            ValueError, match="Start and end strings are lexicographically inseparable"
        ):
            alphabet.mudder("x" + "a" * i, "xa")
        with pytest.raises(
            ValueError, match="Start and end strings are lexicographically inseparable"
        ):
            alphabet.mudder("xa", "x" + "a" * i)


def test_fixes_3__allow_calling_mudder_with_just_number() -> None:
    for abc in (alphabet.mudder(100), base36.mudder(100), base62.mudder(100)):
        assert all(a < b for a, b in pairwise(abc))
    assert alphabet.mudder()


def test_more_3__no_need_to_define_start_or_end() -> None:
    assert base36.mudder("", "foo", 30)
    assert base36.mudder("foo", "", 30)


def test_fixes_7__specify_number_of_divisions() -> None:
    fine = decimal.mudder("9", num_strings=100)
    partial_fine = decimal.mudder("9", num_strings=5, num_divisions=101)
    coarse = decimal.mudder("9", num_strings=5)

    assert all(a < b for a, b in pairwise(fine))
    assert all(a < b for a, b in pairwise(partial_fine))
    assert all(a < b for a, b in pairwise(coarse))
    assert fine[:5] == partial_fine
    assert len(partial_fine) == len(coarse)
    assert partial_fine != coarse

    fine = decimal.mudder("9", "8", 100)
    partial_fine = decimal.mudder("9", "8", 5, num_divisions=101)
    coarse = decimal.mudder("9", "8", 5)

    assert all(a > b for a, b in pairwise(fine))
    assert all(a > b for a, b in pairwise(partial_fine))
    assert all(a > b for a, b in pairwise(coarse))

    # omit last one when going from high to low, the final might be rounded
    assert fine[:4] == partial_fine[:4]


def test_fix_8__better_default_end() -> None:
    assert base36.mudder("z" * 10)[0] != base36.mudder("z" * 15)[0]

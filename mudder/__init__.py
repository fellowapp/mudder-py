import math
from collections.abc import Iterable, Reversible
from decimal import ROUND_HALF_UP, Decimal
from functools import partial
from itertools import chain, cycle
from operator import add

__all__ = [
    "SymbolTable",
    "alphabet",
    "base36",
    "base62",
    "decimal",
]


def is_prefix_code(strings: Iterable[str]) -> bool:
    strings = list(strings)
    strings.sort()

    for i in range(1, len(strings)):
        prev, current = strings[i - 1 : i + 1]
        if prev == current:
            continue
        if current.startswith(prev):
            return False
    return True


class SymbolTable:
    def __init__(
        self, symbols: Iterable[str], symbol_map: dict[str, int] | None = None
    ) -> None:
        symbols = list(symbols)
        if not symbol_map:
            symbol_map = dict((c, i) for i, c in enumerate(symbols))

        symbol_values = set(symbol_map.values())
        for i in range(len(symbols)):
            if i not in symbol_values:
                msg = f"{len(symbols)} symbols given but {i} not found in symbol table"
                raise ValueError(msg)

        self.num2sym = symbols
        self.sym2num = symbol_map
        self.max_base = len(symbols)
        self.is_prefix_code = is_prefix_code(symbols)

    def number_to_digits(self, num: int, base: int | None = None) -> list[int]:
        base = base or self.max_base
        digits: list[int] = []
        while num >= 1:
            digits.append(num % base)
            num = num // base
        digits.reverse()
        if digits:
            return digits
        return [0]

    def digits_to_string(self, digits: Iterable[int]) -> str:
        return "".join([self.num2sym[n] for n in digits])

    def string_to_digits(self, string: Iterable[str]) -> list[int]:
        if isinstance(string, str):
            if not self.is_prefix_code:
                msg = (
                    "Parsing without prefix code is unsupported. "
                    "Pass in array of stringy symbols?"
                )
                raise ValueError(msg)
            string = (c for c in string if c in self.sym2num)

        return [self.sym2num[c] for c in string]

    def digits_to_number(self, digits: Reversible[int], base: int | None = None) -> int:
        base = base or self.max_base
        current_base = 1
        accum = 0
        for current in reversed(digits):
            accum += current * current_base
            current_base *= base
        return accum

    def number_to_string(self, num: int, base: int | None = None) -> str:
        return self.digits_to_string(self.number_to_digits(num, base=base))

    def string_to_number(self, num: Iterable[str], base: int | None = None) -> int:
        return self.digits_to_number(self.string_to_digits(num), base=base)

    def round_fraction(
        self, numerator: int, denominator: int, base: int | None = None
    ) -> list[int]:
        base = base or self.max_base
        places = math.ceil(math.log(denominator) / math.log(base))
        scale = pow(base, places)
        scaled = int(
            Decimal(numerator / denominator * scale).to_integral_value(
                rounding=ROUND_HALF_UP
            )
        )
        digits = self.number_to_digits(scaled, base)
        return left_pad(digits, places)

    def mudder(
        self,
        a: Iterable[str] | int = "",
        b: Iterable[str] = "",
        num_strings: int = 1,
        base: int | None = None,
        num_divisions: int | None = None,
    ) -> list[str]:
        if isinstance(a, int):
            num_strings = a
            a = ""
            b = ""
        a = a or self.num2sym[0]
        b = b or self.num2sym[-1] * (len(list(a)) + 6)
        base = base or self.max_base
        num_divisions = num_divisions or num_strings + 1

        ad = self.string_to_digits(a)
        bd = self.string_to_digits(b)
        intermediate_digits = long_linspace(ad, bd, base, num_strings, num_divisions)
        final_digits = [
            v + self.round_fraction(rem, den, base)
            for v, rem, den in intermediate_digits
        ]
        final_digits.insert(0, ad)
        final_digits.append(bd)
        return [
            self.digits_to_string(v) for v in chop_successive_digits(final_digits)[1:-1]
        ]


def long_div(
    numerator: list[int], denominator: int, base: int
) -> tuple[list[int], int]:
    result = []
    remainder = 0
    for current in numerator:
        new_numerator = current + remainder * base
        result.append(new_numerator // denominator)
        remainder = new_numerator % denominator
    return result, remainder


def long_sub_same_len(
    a: list[int],
    b: list[int],
    base: int,
    remainder: tuple[int, int] | None = None,
    denominator: int = 0,
) -> tuple[list[int], int]:
    if len(a) != len(b):
        msg = "a and b should have same length"
        raise ValueError(msg)

    a = a.copy()  # pre-emptively copy
    if remainder:
        a.append(remainder[0])
        b = b.copy()
        b.append(remainder[1])

    ret = [0] * len(a)

    for i in reversed(range(len(a))):
        if a[i] >= b[i]:
            ret[i] = a[i] - b[i]
            continue
        if i == 0:
            msg = "Cannot go negative"
            raise ValueError(msg)
        do_break = False
        # look for a digit to the left to borrow from
        for j in reversed(range(i)):
            if a[j] > 0:
                # found a non-zero digit. Decrement it
                a[j] -= 1
                # increment all digits to the right by `base-1`
                for k in range(j + 1, i):
                    a[k] += base - 1
                # until you reach the digit you couldn't subtract
                ret[i] = (
                    a[i]
                    + (denominator if remainder and i == len(a) - 1 else base)
                    - b[i]
                )
                do_break = True
                break
        if do_break:
            continue
        msg = "Failed to find digit to borrow from"
        raise ValueError(msg)
    if remainder:
        # result, remainder
        return ret[:-1], ret[-1]
    return ret, 0


def long_add_same_len(
    a: list[int], b: list[int], base: int, remainder: int, denominator: int
) -> tuple[list[int], bool, int, int]:
    if len(a) != len(b):
        msg = "a and b should have same length"
        raise ValueError(msg)

    carry = remainder >= denominator
    res = b.copy()
    if carry:
        remainder -= denominator

    for i, ai in reversed(list(enumerate(a))):
        result = ai + b[i] + int(carry)
        carry = result >= base
        res[i] = result - base if carry else result

    return res, carry, remainder, denominator


def right_pad(arr: list[int], to_length: int, val: int = 0) -> list[int]:
    pad_len = to_length - len(arr)
    if pad_len > 0:
        return arr + [val] * pad_len
    return arr


def long_linspace(
    a: list[int], b: list[int], base: int, n: int, m: int
) -> list[tuple[list[int], int, int]]:
    if len(a) < len(b):
        a = right_pad(a, len(b))
    elif len(b) < len(a):
        b = right_pad(b, len(a))
    if a == b:
        msg = "Start and end strings are lexicographically inseparable"
        raise ValueError(msg)
    a_div, a_div_rem = long_div(a, m, base)
    b_div, b_div_rem = long_div(b, m, base)

    a_prev, a_prev_rem = long_sub_same_len(a, a_div, base, (0, a_div_rem), m)
    b_prev, b_prev_rem = b_div, b_div_rem

    ret = []
    for _i in range(1, n + 1):
        sum_, _carry, rem, den = long_add_same_len(
            a_prev, b_prev, base, a_prev_rem + b_prev_rem, m
        )
        ret.append((sum_, rem, den))
        a_prev, a_prev_rem = long_sub_same_len(
            a_prev, a_div, base, (a_prev_rem, a_div_rem), m
        )
        b_prev, _carry, b_prev_rem, _den = long_add_same_len(
            b_prev, b_div, base, b_prev_rem + b_div_rem, m
        )
    return ret


def left_pad(arr: list[int], to_length: int, val: int = 0) -> list[int]:
    pad_len = to_length - len(arr)
    if pad_len > 0:
        return [val] * pad_len + arr
    return arr


def chop_digits(rock: list[int], water: list[int]) -> list[int]:
    for i in range(len(water)):
        if water[i] and (i >= len(rock) or rock[i] != water[i]):
            return water[: i + 1]
    return water


def lexicographic_less_than_array(a: list[int], b: list[int]) -> bool:
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] == b[i]:
            continue
        return a[i] < b[i]
    return len(a) < len(b)


def chop_successive_digits(strings: list[list[int]]) -> list[list[int]]:
    reversed_ = not lexicographic_less_than_array(strings[0], strings[1])
    if reversed_:
        strings.reverse()
    result = strings[:1]
    for i in range(1, len(strings)):
        result.append(chop_digits(result[-1], strings[i]))
    if reversed_:
        result.reverse()
    return result


digits = "0123456789"
alpha_lower = "abcdefghijklmnopqrstuvwxyz"
alpha_upper = alpha_lower.upper()

decimal = SymbolTable(digits)
base62 = SymbolTable(digits + alpha_upper + alpha_lower)
base36 = SymbolTable(
    digits + alpha_lower,
    dict(
        zip(
            digits + alpha_lower + alpha_upper,
            # 0-9, then 10-35 repeating (for upper and lower case)
            chain(range(10), cycle(map(partial(add, 10), range(26)))),
            strict=False,
        )
    ),
)
alphabet = SymbolTable(
    alpha_lower, dict(zip(alpha_lower + alpha_upper, cycle(range(26))))
)

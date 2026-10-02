"""Validadores de documentos e normalizações."""

import re

_NON_DIGITS = re.compile(r"\D")


def only_digits(value: str) -> str:
    return _NON_DIGITS.sub("", value)


def is_valid_cnpj(cnpj: str) -> bool:
    digits = only_digits(cnpj)
    if len(digits) != 14 or digits == digits[0] * 14:
        return False

    def check(base: str, weights: list[int]) -> str:
        total = sum(int(d) * w for d, w in zip(base, weights, strict=True))
        rest = total % 11
        return "0" if rest < 2 else str(11 - rest)

    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    w2 = [6, *w1]
    d1 = check(digits[:12], w1)
    d2 = check(digits[:12] + d1, w2)
    return digits[12:] == d1 + d2


def is_valid_cpf(cpf: str) -> bool:
    digits = only_digits(cpf)
    if len(digits) != 11 or digits == digits[0] * 11:
        return False
    for size in (9, 10):
        total = sum(int(digits[i]) * (size + 1 - i) for i in range(size))
        dv = (total * 10) % 11 % 10
        if dv != int(digits[size]):
            return False
    return True

import pytest

from app.services.validators import is_valid_cnpj, is_valid_cpf, only_digits


@pytest.mark.parametrize("cnpj", ["11.222.333/0001-81", "11222333000181", "45.723.174/0001-10"])
def test_valid_cnpj(cnpj):
    assert is_valid_cnpj(cnpj)


@pytest.mark.parametrize("cnpj", ["11.222.333/0001-80", "11111111111111", "123", ""])
def test_invalid_cnpj(cnpj):
    assert not is_valid_cnpj(cnpj)


def test_cpf():
    assert is_valid_cpf("529.982.247-25")
    assert not is_valid_cpf("529.982.247-24")
    assert not is_valid_cpf("111.111.111-11")


def test_only_digits():
    assert only_digits("11.222.333/0001-81") == "11222333000181"

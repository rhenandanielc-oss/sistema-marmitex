"""Concorrência real: duas conexões editando a mesma venda (ARCHITECTURE.md D-08, TEST-PLAN.md seção 10)."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.errors import VersionConflict
from app.models import AuditLog, Company, Sale
from app.services.common import commit


@pytest.fixture
def committed_sale(engine):
    """Cria dados com COMMIT real (fora da transação revertida dos outros testes) e limpa ao final."""
    with Session(engine) as s:
        company = Company(name="Concorrência Ltda")
        s.add(company)
        s.flush()
        sale = Sale(buyer_type="COMPANY", company_id=company.id, sale_date=date(2026, 9, 1),
                    unit_price=Decimal("10.00"), quantity=1, subtotal=Decimal("10.00"))
        s.add(sale)
        s.commit()
        ids = (company.id, sale.id)
    yield ids
    with Session(engine) as s:
        s.execute(delete(AuditLog).where(AuditLog.entity_type == "sale", AuditLog.entity_id == str(ids[1])))
        s.execute(delete(Sale).where(Sale.id == ids[1]))
        s.execute(delete(Company).where(Company.id == ids[0]))
        s.commit()


def test_two_simultaneous_edits_one_wins(engine, committed_sale):
    _, sale_id = committed_sale
    first, second = Session(engine), Session(engine)
    try:
        a = first.get(Sale, sale_id)
        b = second.get(Sale, sale_id)
        assert a.version == b.version == 1  # os dois leram a mesma versão

        a.quantity, a.subtotal = 2, Decimal("20.00")
        commit(first)  # primeiro salva

        b.quantity, b.subtotal = 3, Decimal("30.00")
        with pytest.raises(VersionConflict):
            commit(second)  # segundo é recusado (409), sem sobrescrever
    finally:
        first.close()
        second.close()

    with Session(engine) as check:
        final = check.get(Sale, sale_id)
        assert (final.quantity, final.subtotal, final.version) == (2, Decimal("20.00"), 2)

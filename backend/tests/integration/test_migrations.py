from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from alembic import command
from app.models import Base
from tests.conftest import TEST_DATABASE_URL, alembic_config, recreate_database

MIGRATION_DB_URL = make_url(TEST_DATABASE_URL).set(database="marmitex_migrations_test").render_as_string(
    hide_password=False)


def test_upgrade_downgrade_upgrade_and_models_match():
    recreate_database(MIGRATION_DB_URL)
    cfg = alembic_config(url=MIGRATION_DB_URL)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")

    engine = create_engine(MIGRATION_DB_URL)
    try:
        with engine.connect() as conn:
            diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
            assert diff == [], f"Modelos e migrations divergem: {diff}"
            seeded = conn.execute(text("SELECT name, cost_type FROM cost_categories ORDER BY id")).all()
    finally:
        engine.dispose()
    assert len(seeded) == 10
    assert ("Ingredientes", "CUSTO_DIARIO") in seeded
    assert ("Aluguel", "CUSTO_FIXO") in seeded
    assert sum(1 for _, t in seeded if t == "CUSTO_FIXO") == 5

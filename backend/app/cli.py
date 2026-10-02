"""Comandos administrativos.

Uso:
    python -m app.cli create-admin            # lê INITIAL_ADMIN_* do ambiente ou pergunta
"""

import getpass
import os
import sys

from app.core.db import SessionLocal
from app.core.security import MIN_PASSWORD_LENGTH, hash_password
from app.models import User
from app.models.enums import AuditAction, Role
from app.services import audit
from app.services.auth_service import find_user_by_email


def create_admin() -> int:
    name = os.environ.get("INITIAL_ADMIN_NAME") or input("Nome: ").strip()
    email = os.environ.get("INITIAL_ADMIN_EMAIL") or input("E-mail: ").strip()
    password = os.environ.get("INITIAL_ADMIN_PASSWORD") or getpass.getpass("Senha: ")
    if len(password) < MIN_PASSWORD_LENGTH:
        print(f"A senha deve ter pelo menos {MIN_PASSWORD_LENGTH} caracteres.", file=sys.stderr)
        return 1
    with SessionLocal() as db:
        if find_user_by_email(db, email):
            print("Já existe um usuário com este e-mail.", file=sys.stderr)
            return 1
        user = User(name=name or "Administrador", email=email.lower(), password_hash=hash_password(password),
                    role=Role.ADMIN)
        db.add(user)
        db.flush()
        audit.record(db, action=AuditAction.CREATE, entity_type="user", entity_id=user.id,
                     after=audit.snapshot(user))
        db.commit()
    print(f"Administrador {email} criado.")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[1] == "create-admin":
        return create_admin()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

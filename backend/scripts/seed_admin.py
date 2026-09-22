"""Crea una cuenta de administrador. No hay administrador por defecto: hay que crearlo a mano.

Uso interactivo (desde backend/), pide la contraseña dos veces sin mostrarla:
    .venv\\Scripts\\python.exe -m scripts.seed_admin --email admin@correo.com --first-name Ana --last-name Pérez

Para automatizarlo, la contraseña se lee de la entrada estándar (no se acepta por argumento, para que no
quede en el historial de la terminal ni en la lista de procesos):
    "clave-segura-1" | .venv\\Scripts\\python.exe -m scripts.seed_admin --password-stdin --email … --first-name … --last-name …

Escribe en `backend/data/users.json`, o en la carpeta que indique la variable de entorno `DATA_DIR`.
"""

from __future__ import annotations

import argparse
import getpass
import sys

from pydantic import ValidationError

from app.core.deps import get_auth_service
from app.schemas.auth import AddressIn, RegisterIn
from app.services.auth_service import EmailTaken


def read_password(from_stdin: bool) -> str | None:
    if from_stdin:
        return sys.stdin.readline().rstrip("\r\n")
    password = getpass.getpass("Contraseña (mínimo 8 caracteres): ")
    if password != getpass.getpass("Repite la contraseña: "):
        print("Las contraseñas no coinciden.")
        return None
    return password


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Crea un administrador")
    parser.add_argument("--email", required=True)
    parser.add_argument("--first-name", required=True)
    parser.add_argument("--last-name", required=True)
    parser.add_argument("--address", default="Sede Open Books")
    parser.add_argument("--city", default="Bogotá")
    parser.add_argument("--password-stdin", action="store_true", help="lee la contraseña de la entrada estándar")
    args = parser.parse_args(argv)

    password = read_password(args.password_stdin)
    if password is None:
        return 1

    try:
        data = RegisterIn(
            first_name=args.first_name,
            last_name=args.last_name,
            email=args.email,
            address=AddressIn(line=args.address, city=args.city),
            password=password,
        )
    except ValidationError as error:
        print("Datos inválidos:")
        for problem in error.errors():
            print(f"  - {'.'.join(str(p) for p in problem['loc'])}: {problem['msg']}")
        return 1

    try:
        user = get_auth_service().register(data, role="admin")
    except EmailTaken:
        print("Ya existe una cuenta con ese correo.")
        return 1

    print(f"Administrador creado: {user.email} ({user.id})")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())

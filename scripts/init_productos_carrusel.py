"""
Crea la tabla plan_beneficios.productos_carrusel en PostgreSQL (bind db3).

Uso (desde la raíz del proyecto):
    python scripts/init_productos_carrusel.py
"""
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app import app, ensure_productos_carrusel_table


def main():
    with app.app_context():
        ensure_productos_carrusel_table()
    print("OK: tabla plan_beneficios.productos_carrusel lista.")


if __name__ == "__main__":
    main()

"""
Duplica el único producto del carrusel para tener 15 filas de prueba (misma imagen,
precios y puntos; nombre y código con sufijo para distinguirlos en admin).

Requisitos: exactamente 1 fila en plan_beneficios.productos_carrusel.
Si ya hay 15 o más productos, no hace nada.

Uso (desde la raíz del proyecto):
    python scripts/clone_producto_carrusel_demo.py

Opcional:
    python scripts/clone_producto_carrusel_demo.py --total 15
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import uuid
from datetime import datetime

# Permite ejecutar: python scripts/clone_producto_carrusel_demo.py (Python pone scripts/ en el path, no la raíz).
_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app import ProductoCarrusel, app, db, ensure_productos_carrusel_table


def main() -> None:
    parser = argparse.ArgumentParser(description="Clona el único producto del carrusel N veces.")
    parser.add_argument(
        "--total",
        type=int,
        default=15,
        metavar="N",
        help="Número total de productos que deben quedar (por defecto 15).",
    )
    args = parser.parse_args()
    target = max(1, args.total)

    with app.app_context():
        ensure_productos_carrusel_table()
        count = ProductoCarrusel.query.count()
        if count == 0:
            print("Error: no hay productos en productos_carrusel. Crea uno desde el admin.")
            sys.exit(1)
        if count != 1:
            print(
                f"Error: este script espera exactamente 1 producto plantilla; hay {count}. "
                "Deja solo el que quieras clonar o ajusta el script."
            )
            sys.exit(1)

        base = ProductoCarrusel.query.order_by(ProductoCarrusel.creado_en.asc()).first()
        if count > target:
            print(f"Ya hay {count} productos (más que el objetivo {target}). No se insertan copias.")
            return
        if count == target:
            print(f"Ya hay exactamente {target} producto(s). Nada que hacer.")
            return

        to_create = target - count
        nuevos = []
        base_codigo = (base.codigo_producto or "DEMO").strip()[:80]
        for i in range(1, to_create + 1):
            suf = count + i
            nombre = f"{base.nombre} (demo {suf})"
            if len(nombre) > 200:
                nombre = nombre[:197] + "..."
            codigo = f"{base_codigo}-D{suf:02d}"[:100]
            nuevos.append(
                ProductoCarrusel(
                    id=uuid.uuid4(),
                    nombre=nombre,
                    imagen_url=base.imagen_url,
                    precio_original=base.precio_original,
                    puntos_requeridos=base.puntos_requeridos,
                    codigo_producto=codigo,
                    estado=bool(base.estado),
                    creado_en=datetime.now(),
                    actualizado_en=None,
                )
            )
        db.session.add_all(nuevos)
        db.session.commit()
        final = ProductoCarrusel.query.count()
        print(f"OK: se insertaron {to_create} copias. Total productos carrusel: {final}.")


if __name__ == "__main__":
    main()

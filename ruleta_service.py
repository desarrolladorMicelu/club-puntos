import random
import re
from datetime import datetime

import pytz

ZONA_BOGOTA = pytz.timezone('America/Bogota')

# Lista de premios reales con pesos. "Sin premio" debe salir casi siempre;
# ganar un premio físico debe ser muy poco probable.
PREMIOS = [
    {'nombre': 'Sin premio', 'peso': 970},
    {'nombre': 'Audífonos de Cable Plug', 'peso': 1},
    {'nombre': 'Cabezote Dual C-USB Miccell', 'peso': 1},
    {'nombre': 'Apple AirPods Serie 2 Premium 1.1', 'peso': 1},
    {'nombre': 'Kit Cargador Inalámbrico Verizon (Carro y Pared)', 'peso': 1},
    {'nombre': 'Diadema Bluetooth VQ-B15 Miccell', 'peso': 1},
    {'nombre': 'PopSocket', 'peso': 1},
    {'nombre': 'Estuche Protector AirPods (Todas las Referencias)', 'peso': 1},
    {'nombre': 'Llaveros', 'peso': 1},
    {'nombre': 'Estuche Protector de Cargador', 'peso': 1},
    {'nombre': 'Estuche Space Transparente (Todas las Referencias)', 'peso': 1},
    {'nombre': 'Cargador Completo C a C Miccell', 'peso': 1},
    {'nombre': 'Audífonos de Cable Lightning', 'peso': 1},
    {'nombre': 'Audífonos Bluetooth VQ-BH32 Miccell', 'peso': 1},
    {'nombre': 'Apple AirPods Serie 3 Genérico 1.1', 'peso': 1},
]


def normalizar_premio(premio):
    """Normaliza una cadena de premio para evitar diferencias de formato."""
    if premio is None:
        return 'Sin premio'
    texto = str(premio).strip()
    return texto or 'Sin premio'


def validar_documento(documento):
    """Valida que el documento sea numérico y tenga longitud razonable."""
    if documento is None:
        return False, 'Debe ingresar un documento.'

    valor = str(documento).strip()
    if not valor or not re.fullmatch(r'\d{6,10}', valor):
        return False, 'El documento debe tener entre 6 y 10 dígitos numéricos.'
    return True, valor


def validar_nombre(nombre):
    """Valida nombre, pero no obliga a usarlo. Si viene vacío se reemplaza por un valor genérico."""
    if nombre is None:
        return True, 'Cliente'

    valor = str(nombre).strip()
    if not valor:
        return True, 'Cliente'
    return True, valor


def seleccionar_premio():
    """Selecciona un premio con pesos definidos."""
    total = sum(item['peso'] for item in PREMIOS)
    numero = random.randint(1, total)
    acumulado = 0
    for item in PREMIOS:
        acumulado += item['peso']
        if numero <= acumulado:
            return normalizar_premio(item['nombre'])
    return 'Sin premio'


def formatear_fecha_bogota(fecha):
    """Formatea una fecha para mostrarla en hora local de Bogotá."""
    if not fecha:
        return 'Fecha no disponible'
    if isinstance(fecha, str):
        try:
            fecha = datetime.fromisoformat(fecha)
        except ValueError:
            return fecha
    bogota = ZONA_BOGOTA.localize(fecha.replace(tzinfo=None)) if fecha.tzinfo is None else fecha.astimezone(ZONA_BOGOTA)
    return bogota.strftime('%d/%m/%Y %H:%M')

"""
============================================================================
SERVICIO POLLA MUNDIAL 2026 - Club de Puntos Micelu
============================================================================
Integra la API de football-data.org (v4) para obtener partidos y resultados
del Mundial 2026, y contiene el motor de calificación (scoring) de la polla.

Diseñado para ser robusto:
- Si no hay token de API configurado, el sistema NO se cae: usa datos demo.
- La sincronización es idempotente (upsert por api_id).
- La calificación es idempotente (solo califica partidos no procesados).
============================================================================
"""
import os
from datetime import datetime, timedelta

import requests

# ----------------------------------------------------------------------------
# CONFIGURACIÓN
# ----------------------------------------------------------------------------
API_BASE = "https://api.football-data.org/v4"
COMPETICION = "WC"  # World Cup (id 2000 en football-data.org)
TIMEOUT = 12

# Reglas de puntuación de la polla
PUNTOS_EXACTO_GRUPOS = 5        # Marcador exacto en fase de grupos
PUNTOS_RESULTADO_GRUPOS = 3     # Acertar ganador/empate en fase de grupos
PUNTOS_EXACTO_ELIMINATORIA = 8  # Marcador exacto en eliminación directa
PUNTOS_RESULTADO_ELIMINATORIA = 5  # Acertar ganador/empate en eliminación

STAGES_GRUPOS = ('GROUP_STAGE', 'LEAGUE_STAGE', 'GROUP', 'REGULAR_SEASON')
ESTADOS_ABIERTOS = ('SCHEDULED', 'TIMED')  # Estados donde aún se puede pronosticar
BUFFER_CIERRE_MIN = 5  # Minutos antes del inicio en que se cierra el pronóstico


def obtener_token():
    """Obtiene el token de la API. Hardcodeado temporalmente para despliegue."""
    return '84e8166981f940b69d87f829684678f0'


def _parse_utc(iso_str):
    """Convierte un string ISO (con o sin Z) a datetime naive en UTC."""
    if not iso_str:
        return None
    try:
        limpio = iso_str.replace('Z', '').replace('+00:00', '')
        return datetime.strptime(limpio, '%Y-%m-%dT%H:%M:%S')
    except (ValueError, TypeError):
        try:
            return datetime.strptime(iso_str[:19], '%Y-%m-%dT%H:%M:%S')
        except (ValueError, TypeError):
            return None


def es_eliminatoria(stage):
    """Determina si un partido pertenece a fase de eliminación directa."""
    if not stage:
        return False
    return stage.upper() not in STAGES_GRUPOS


def calcular_ganador(goles_local, goles_visitante):
    """Devuelve 'HOME', 'AWAY' o 'DRAW' según el marcador."""
    if goles_local is None or goles_visitante is None:
        return None
    if goles_local > goles_visitante:
        return 'HOME'
    if goles_local < goles_visitante:
        return 'AWAY'
    return 'DRAW'


def calcular_puntos_pronostico(pred_local, pred_visitante,
                               real_local, real_visitante, stage):
    """
    Calcula los puntos de un pronóstico contra el resultado real.

    Returns:
        tuple: (puntos:int, tipo_acierto:str)  tipo en {'EXACTO','RESULTADO','FALLO'}
    """
    if None in (pred_local, pred_visitante, real_local, real_visitante):
        return 0, 'FALLO'

    eliminatoria = es_eliminatoria(stage)
    p_exacto = PUNTOS_EXACTO_ELIMINATORIA if eliminatoria else PUNTOS_EXACTO_GRUPOS
    p_result = PUNTOS_RESULTADO_ELIMINATORIA if eliminatoria else PUNTOS_RESULTADO_GRUPOS

    # Marcador exacto
    if pred_local == real_local and pred_visitante == real_visitante:
        return p_exacto, 'EXACTO'

    # Acertar la tendencia (ganador o empate)
    if calcular_ganador(pred_local, pred_visitante) == calcular_ganador(real_local, real_visitante):
        return p_result, 'RESULTADO'

    return 0, 'FALLO'


# ----------------------------------------------------------------------------
# CONSUMO DE LA API
# ----------------------------------------------------------------------------
def _normalizar_partido(m):
    """Convierte un objeto match de football-data.org a un dict estándar interno."""
    home = m.get('homeTeam') or {}
    away = m.get('awayTeam') or {}
    score = m.get('score') or {}
    full = score.get('fullTime') or {}

    return {
        'api_id': m.get('id'),
        'utc_date': _parse_utc(m.get('utcDate')),
        'estado': m.get('status') or 'SCHEDULED',
        'stage': m.get('stage') or 'GROUP_STAGE',
        'grupo': m.get('group'),
        'matchday': m.get('matchday'),
        'equipo_local': home.get('name') or 'Por definir',
        'equipo_local_tla': home.get('tla') or '',
        'equipo_local_crest': home.get('crest') or '',
        'equipo_visitante': away.get('name') or 'Por definir',
        'equipo_visitante_tla': away.get('tla') or '',
        'equipo_visitante_crest': away.get('crest') or '',
        'goles_local': full.get('home'),
        'goles_visitante': full.get('away'),
    }


def obtener_partidos_api():
    """
    Obtiene los partidos del Mundial desde football-data.org.

    Returns:
        tuple: (partidos:list[dict], fuente:str, error:str|None)
        fuente in {'API','DEMO'}
    """
    token = obtener_token()
    if not token:
        # Sin token -> datos demo para que la sección funcione siempre.
        return generar_partidos_demo(), 'DEMO', 'Token de API no configurado (usando datos demo).'

    try:
        url = f"{API_BASE}/competitions/{COMPETICION}/matches"
        resp = requests.get(url, headers={'X-Auth-Token': token}, timeout=TIMEOUT)
        if resp.status_code != 200:
            return (generar_partidos_demo(), 'DEMO',
                    f'API respondió {resp.status_code}. Usando datos demo.')
        data = resp.json()
        matches = data.get('matches', [])
        if not matches:
            return generar_partidos_demo(), 'DEMO', 'API sin partidos disponibles aún. Usando datos demo.'
        partidos = [_normalizar_partido(m) for m in matches if m.get('id')]
        return partidos, 'API', None
    except requests.RequestException as e:
        return generar_partidos_demo(), 'DEMO', f'Error de conexión con la API: {e}. Usando datos demo.'
    except Exception as e:
        return generar_partidos_demo(), 'DEMO', f'Error inesperado: {e}. Usando datos demo.'


# ----------------------------------------------------------------------------
# DATOS DEMO (fallback) - 16 partidos representativos del Mundial 2026
# ----------------------------------------------------------------------------
def generar_partidos_demo():
    """
    Genera un fixture demo con sabor a Mundial 2026.
    Mezcla algunos partidos ya 'jugados' (FINISHED) y otros próximos.
    Colombia incluida con protagonismo.
    """
    base = datetime.utcnow()

    equipos = [
        ('Colombia', 'COL', 'https://crests.football-data.org/colombia.svg'),
        ('Argentina', 'ARG', 'https://crests.football-data.org/762.svg'),
        ('Brasil', 'BRA', 'https://crests.football-data.org/764.svg'),
        ('Estados Unidos', 'USA', 'https://crests.football-data.org/usa.svg'),
        ('México', 'MEX', 'https://crests.football-data.org/mex.svg'),
        ('Francia', 'FRA', 'https://crests.football-data.org/773.svg'),
        ('España', 'ESP', 'https://crests.football-data.org/760.svg'),
        ('Alemania', 'GER', 'https://crests.football-data.org/759.svg'),
        ('Uruguay', 'URU', 'https://crests.football-data.org/758.svg'),
        ('Inglaterra', 'ENG', 'https://crests.football-data.org/770.svg'),
        ('Portugal', 'POR', 'https://crests.football-data.org/765.svg'),
        ('Países Bajos', 'NED', 'https://crests.football-data.org/8601.svg'),
    ]

    enfrentamientos = [
        ('Colombia', 'México', 'Grupo A', -3, (2, 1)),
        ('Estados Unidos', 'Brasil', 'Grupo B', -3, (0, 2)),
        ('Argentina', 'Alemania', 'Grupo C', -2, (1, 1)),
        ('Francia', 'España', 'Grupo D', -2, (3, 2)),
        ('Colombia', 'Uruguay', 'Grupo A', -1, (1, 0)),
        ('Inglaterra', 'Portugal', 'Grupo E', -1, (2, 2)),
        ('Brasil', 'México', 'Grupo B', 1, None),
        ('Colombia', 'Estados Unidos', 'Grupo A', 2, None),
        ('Argentina', 'Países Bajos', 'Grupo C', 2, None),
        ('España', 'Alemania', 'Grupo D', 3, None),
        ('Portugal', 'Francia', 'Grupo E', 4, None),
        ('Uruguay', 'Inglaterra', 'Grupo F', 5, None),
    ]

    mapa = {nombre: (tla, crest) for nombre, tla, crest in equipos}
    partidos = []
    for i, (local, visitante, grupo, dia_offset, marcador) in enumerate(enfrentamientos, start=1):
        ltla, lcrest = mapa.get(local, ('', ''))
        vtla, vcrest = mapa.get(visitante, ('', ''))
        finished = marcador is not None
        partidos.append({
            'api_id': 900000 + i,  # IDs demo altos para no chocar con la API real
            'utc_date': base + timedelta(days=dia_offset),
            'estado': 'FINISHED' if finished else 'SCHEDULED',
            'stage': 'GROUP_STAGE',
            'grupo': grupo,
            'matchday': 1,
            'equipo_local': local,
            'equipo_local_tla': ltla,
            'equipo_local_crest': lcrest,
            'equipo_visitante': visitante,
            'equipo_visitante_tla': vtla,
            'equipo_visitante_crest': vcrest,
            'goles_local': marcador[0] if finished else None,
            'goles_visitante': marcador[1] if finished else None,
        })
    return partidos

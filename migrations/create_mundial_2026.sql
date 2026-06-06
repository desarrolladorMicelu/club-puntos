-- ============================================================================
-- MIGRACIÓN: Polla Mundial 2026 - Club de Puntos Micelu
-- ============================================================================
-- Ejecutar en PostgreSQL (db3), esquema plan_beneficios.
-- Idempotente: usa IF NOT EXISTS.

-- ----------------------------------------------------------------------------
-- 1. TABLA DE PARTIDOS (sincronizados desde football-data.org)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS plan_beneficios.mundial_partidos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_id BIGINT NOT NULL UNIQUE,
    fecha_partido TIMESTAMP NULL,
    estado VARCHAR(20) DEFAULT 'SCHEDULED',
    stage VARCHAR(40) NULL,
    grupo VARCHAR(20) NULL,
    matchday INTEGER NULL,

    equipo_local VARCHAR(80) NOT NULL,
    equipo_local_tla VARCHAR(10) NULL,
    equipo_local_crest VARCHAR(300) NULL,
    equipo_visitante VARCHAR(80) NOT NULL,
    equipo_visitante_tla VARCHAR(10) NULL,
    equipo_visitante_crest VARCHAR(300) NULL,

    goles_local INTEGER NULL,
    goles_visitante INTEGER NULL,

    puntos_calculados BOOLEAN DEFAULT FALSE,

    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP NULL
);

CREATE INDEX IF NOT EXISTS idx_mundial_partidos_api ON plan_beneficios.mundial_partidos(api_id);
CREATE INDEX IF NOT EXISTS idx_mundial_partidos_fecha ON plan_beneficios.mundial_partidos(fecha_partido);
CREATE INDEX IF NOT EXISTS idx_mundial_partidos_calc ON plan_beneficios.mundial_partidos(puntos_calculados);

-- ----------------------------------------------------------------------------
-- 2. TABLA DE PRONÓSTICOS (un usuario => un pronóstico por partido)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS plan_beneficios.mundial_pronosticos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento VARCHAR(50) NOT NULL,
    api_id BIGINT NOT NULL,

    pred_local INTEGER NOT NULL,
    pred_visitante INTEGER NOT NULL,

    puntos_obtenidos INTEGER DEFAULT 0,
    tipo_acierto VARCHAR(20) NULL,
    calificado BOOLEAN DEFAULT FALSE,

    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP NULL,

    CONSTRAINT uq_pronostico_usuario_partido UNIQUE (documento, api_id)
);

CREATE INDEX IF NOT EXISTS idx_mundial_pron_doc ON plan_beneficios.mundial_pronosticos(documento);
CREATE INDEX IF NOT EXISTS idx_mundial_pron_api ON plan_beneficios.mundial_pronosticos(api_id);
CREATE INDEX IF NOT EXISTS idx_mundial_pron_calif ON plan_beneficios.mundial_pronosticos(calificado);

-- ----------------------------------------------------------------------------
-- Comentarios de documentación
-- ----------------------------------------------------------------------------
COMMENT ON TABLE plan_beneficios.mundial_partidos IS 'Partidos del Mundial 2026 sincronizados desde la API.';
COMMENT ON TABLE plan_beneficios.mundial_pronosticos IS 'Pronósticos de la polla mundialista por usuario y partido.';
COMMENT ON COLUMN plan_beneficios.mundial_pronosticos.tipo_acierto IS 'EXACTO (marcador exacto), RESULTADO (acertó ganador/empate), FALLO.';

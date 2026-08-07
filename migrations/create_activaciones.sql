-- ============================================================
-- Migración: Tabla de Activaciones de Puntos
-- Ejecutar una sola vez en la base de datos 'db3' (plan_beneficios)
-- ============================================================

CREATE TABLE IF NOT EXISTS plan_beneficios.activaciones (
    id              VARCHAR(36)     PRIMARY KEY,
    multiplicador   INTEGER         NOT NULL CHECK (multiplicador >= 2),
    fecha_inicio    TIMESTAMP       NOT NULL,
    fecha_fin       TIMESTAMP       NOT NULL,
    estado          VARCHAR(20)     NOT NULL DEFAULT 'ACTIVA'
                                    CHECK (estado IN ('ACTIVA', 'PAUSADA')),
    creado_por      VARCHAR(50),
    creado_en       TIMESTAMP       NOT NULL DEFAULT NOW(),
    actualizado_en  TIMESTAMP,
    CONSTRAINT chk_fechas CHECK (fecha_fin > fecha_inicio)
);

-- Índice para acelerar la consulta de activación vigente
CREATE INDEX IF NOT EXISTS idx_activaciones_estado_fechas
    ON plan_beneficios.activaciones (estado, fecha_inicio, fecha_fin);

COMMENT ON TABLE plan_beneficios.activaciones IS
    'Períodos promocionales donde los puntos se multiplican (ej: x2, x3). Solo una activa simultáneamente.';

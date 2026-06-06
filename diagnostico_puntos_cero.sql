-- ============================================================================
-- DIAGNÓSTICO: Por qué el sistema nuevo trae 0 puntos
-- ============================================================================
-- Hipótesis: las transacciones migradas tienen fecha_vencimiento en el pasado
-- (fecha_registro + 365 días), por lo que el cálculo las excluye aunque
-- su estado siga siendo 'ACTIVO'.

-- 1. Reemplaza 'DOCUMENTO_AQUI' por el documento del cliente afectado.
--    Compara: lo que SÍ existe vs lo que el sistema "trae".

-- (a) TODO lo que existe para el cliente (sin filtros) -> esto es lo que "ves"
SELECT
    tipo_transaccion,
    puntos,
    estado,
    fecha_transaccion,
    fecha_vencimiento,
    (fecha_vencimiento < CURRENT_TIMESTAMP) AS ya_vencido_por_fecha
FROM plan_beneficios.transacciones_puntos
WHERE documento = 'DOCUMENTO_AQUI'
ORDER BY fecha_transaccion;

-- (b) Lo que el sistema nuevo SÍ suma (debería darte 0 si es el bug)
SELECT COALESCE(SUM(puntos), 0) AS puntos_que_trae_el_sistema
FROM plan_beneficios.transacciones_puntos
WHERE documento = 'DOCUMENTO_AQUI'
  AND estado = 'ACTIVO'
  AND (fecha_vencimiento IS NULL OR fecha_vencimiento >= CURRENT_TIMESTAMP);

-- (c) Lo que debería tener si NO miramos vencimiento
SELECT COALESCE(SUM(puntos), 0) AS puntos_reales_sin_vencimiento
FROM plan_beneficios.transacciones_puntos
WHERE documento = 'DOCUMENTO_AQUI'
  AND estado = 'ACTIVO';

-- 2. Magnitud del problema en TODA la base:
--    Cuántas transacciones ACTIVAS están "vencidas por fecha" (nacieron vencidas)
SELECT
    COUNT(*) AS transacciones_activas_vencidas,
    COUNT(DISTINCT documento) AS clientes_afectados,
    SUM(puntos) AS puntos_atrapados
FROM plan_beneficios.transacciones_puntos
WHERE estado = 'ACTIVO'
  AND fecha_vencimiento IS NOT NULL
  AND fecha_vencimiento < CURRENT_TIMESTAMP;

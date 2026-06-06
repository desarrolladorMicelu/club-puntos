-- ============================================================================
-- FIX: Puntos que aparecen en 0 por fecha_vencimiento en el pasado
-- ============================================================================
-- IMPORTANTE / SEGURIDAD:
--   * Esto es un UPDATE. NO borra filas, NO borra tablas, NO toca puntos
--     ni documentos. SOLO cambia 'fecha_vencimiento' y 'actualizado_en'.
--   * No hay DELETE, ni DROP, ni TRUNCATE. No se pierde ningún dato.
--
-- Causa del bug:
--   En la migración se puso fecha_vencimiento = fecha_registro + 365 días.
--   Para clientes registrados hace más de un año, esa fecha ya está en el
--   pasado, así que el cálculo de puntos disponibles los excluye aunque su
--   estado siga siendo 'ACTIVO' (por eso existen en la BD pero "trae" 0).
--
-- Recomendación: corre primero el bloque 2 de diagnostico_puntos_cero.sql
-- y, si quieres, haz un backup antes. Luego ejecuta UNA de las dos opciones.
-- ============================================================================


-- OPCIÓN A (recomendada): renovar la vigencia a 1 año contado DESDE HOY.
-- Así todos los puntos atrapados vuelven a quedar disponibles y conservan
-- una caducidad razonable hacia adelante.
UPDATE plan_beneficios.transacciones_puntos
SET fecha_vencimiento = CURRENT_TIMESTAMP + INTERVAL '365 days',
    actualizado_en    = CURRENT_TIMESTAMP
WHERE estado = 'ACTIVO'
  AND fecha_vencimiento IS NOT NULL
  AND fecha_vencimiento < CURRENT_TIMESTAMP;


-- OPCIÓN B (alternativa): que esos puntos NO venzan (fecha_vencimiento = NULL).
-- Úsala SOLO si prefieres que no caduquen. Comenta la Opción A y descomenta esta.
-- UPDATE plan_beneficios.transacciones_puntos
-- SET fecha_vencimiento = NULL,
--     actualizado_en    = CURRENT_TIMESTAMP
-- WHERE estado = 'ACTIVO'
--   AND fecha_vencimiento IS NOT NULL
--   AND fecha_vencimiento < CURRENT_TIMESTAMP;


-- ============================================================================
-- VERIFICACIÓN (después de ejecutar el UPDATE)
-- ============================================================================

-- (1) Esto debería dar 0 ahora: ya no hay transacciones activas "vencidas".
SELECT
    COUNT(*)               AS transacciones_activas_vencidas,
    COUNT(DISTINCT documento) AS clientes_afectados,
    COALESCE(SUM(puntos),0)   AS puntos_atrapados
FROM plan_beneficios.transacciones_puntos
WHERE estado = 'ACTIVO'
  AND fecha_vencimiento IS NOT NULL
  AND fecha_vencimiento < CURRENT_TIMESTAMP;

-- (2) Verificar un cliente puntual (reemplaza DOCUMENTO_AQUI):
--     ahora debería traer los puntos en vez de 0.
SELECT COALESCE(SUM(puntos), 0) AS puntos_disponibles_ahora
FROM plan_beneficios.transacciones_puntos
WHERE documento = 'DOCUMENTO_AQUI'
  AND estado = 'ACTIVO'
  AND (fecha_vencimiento IS NULL OR fecha_vencimiento >= CURRENT_TIMESTAMP);
